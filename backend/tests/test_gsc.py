"""
Tests for the Google Search Console integration: OAuth state signing,
property matching, and the daily sync flow (with a mocked HTTP transport —
no live Google calls).
"""
import os
import tempfile
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")

import httpx  # noqa: E402

from app.core.security import sign_state, verify_state, encrypt_secret  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402
from app.models import User, Website, SearchConsoleProfile, GSCMetric, GSCQueryMetric  # noqa: E402
from app.services import gsc as gsc_service  # noqa: E402

TOKEN_URL_HOST = "oauth2.googleapis.com"
SA_HOST = "searchconsole.googleapis.com"


def _seed_site_with_profile() -> int:
    db = SessionLocal()
    user = User(email="gsc@test.com", password_hash="x", plan="free")
    db.add(user)
    db.flush()
    site = Website(user_id=user.id, domain="gsc-example.com", status="active")
    db.add(site)
    db.flush()
    profile = SearchConsoleProfile(
        website_id=site.id,
        access_token_encrypted=encrypt_secret("old-access"),
        refresh_token_encrypted=encrypt_secret("refresh-token"),
        token_expires_at=datetime.utcnow() - timedelta(minutes=5),  # force a refresh
        status="connected",
    )
    db.add(profile)
    db.commit()
    site_id = site.id
    db.close()
    return site_id


def _mock_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host == TOKEN_URL_HOST:
            return httpx.Response(200, json={
                "access_token": "fresh-access",
                "expires_in": 3600,
                "token_type": "Bearer",
            })
        if host == SA_HOST and request.url.path.endswith("/sites"):
            return httpx.Response(200, json={
                "siteEntry": [
                    {"siteUrl": "sc-domain:gsc-example.com", "permissionLevel": "siteFullUser"},
                    {"siteUrl": "https://gsc-example.com/", "permissionLevel": "siteFullUser"},
                ]
            })
        if host == SA_HOST and request.url.path.endswith("/searchAnalytics/query"):
            body = request.read()
            if b'"dimensions": ["date"]' in body:
                return httpx.Response(200, json={"rows": [
                    {"keys": ["2026-01-10"], "clicks": 12, "impressions": 300, "ctr": 0.04, "position": 5.2},
                    {"keys": ["2026-01-11"], "clicks": 20, "impressions": 400, "ctr": 0.05, "position": 4.1},
                ]})
            if b'"dimensions": ["query"]' in body:
                return httpx.Response(200, json={"rows": [
                    {"keys": ["best gsc-example services"], "clicks": 15, "impressions": 250, "ctr": 0.06, "position": 3.2},
                ]})
        return httpx.Response(500, text="unexpected request")
    return httpx.MockTransport(handler)


def test_state_sign_and_verify_roundtrip():
    state = sign_state("42")
    assert verify_state(state) == "42"


def test_state_rejects_tampering():
    state = sign_state("42")
    tampered = state[:-4] + ("ab" if not state.endswith("ab") else "cd")
    assert verify_state(tampered) is None


def test_state_rejects_expired():
    state = sign_state("42", ttl_seconds=-10)
    assert verify_state(state) is None


def test_pick_matching_property():
    urls = ["https://other.com/", "sc-domain:example.com", "https://example.com/"]
    assert gsc_service.pick_matching_property(urls, "example.com") == "sc-domain:example.com"
    assert gsc_service.pick_matching_property(["https://other.com/"], "example.com") is None


def test_sync_pulls_metrics_and_queries():
    site_id = _seed_site_with_profile()
    db = SessionLocal()
    website = db.query(Website).filter(Website.id == site_id).first()

    with httpx.Client(transport=_mock_transport()) as client:
        result = gsc_service.sync_gsc_for_website(db, website, client=client)

    assert result["status"] == "ok"
    assert result["rows"] == 2

    profile = db.query(SearchConsoleProfile).filter(SearchConsoleProfile.website_id == site_id).first()
    assert profile.site_url == "sc-domain:gsc-example.com"
    assert profile.status == "connected"
    assert profile.last_sync_at is not None

    metrics = db.query(GSCMetric).filter(GSCMetric.website_id == site_id).order_by(GSCMetric.date).all()
    assert len(metrics) == 2
    assert metrics[0].clicks == 12 and metrics[0].impressions == 300
    assert metrics[1].clicks == 20 and metrics[1].position == 4.1

    queries = db.query(GSCQueryMetric).filter(GSCQueryMetric.website_id == site_id).all()
    assert len(queries) == 1
    assert queries[0].query == "best gsc-example services"
    assert queries[0].clicks == 15

    db.close()


def test_report_includes_gsc_block():
    from app.api.reports import get_website_report
    from app.models import User as U

    site_id = _seed_site_with_profile()
    db = SessionLocal()
    user = db.query(U).filter(U.email == "gsc@test.com").first()

    report = get_website_report(site_id, user, db)
    assert "gsc" in report
    assert report["gsc"]["connected"] is False  # no sync run, no site_url yet
    assert report["gsc"]["metrics"] == []

    # After a sync, the block carries real data
    website = db.query(Website).filter(Website.id == site_id).first()
    with httpx.Client(transport=_mock_transport()) as client:
        gsc_service.sync_gsc_for_website(db, website, client=client)
    report2 = get_website_report(site_id, user, db)
    assert report2["gsc"]["connected"] is True
    assert len(report2["gsc"]["metrics"]) == 2
    assert report2["gsc"]["top_queries"][0]["query"] == "best gsc-example services"

    db.close()
