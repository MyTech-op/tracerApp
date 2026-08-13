"""
Tests for plan limits and the Stripe billing endpoints.

Hermetic: no real Stripe calls. When STRIPE_SECRET_KEY is unset, checkout/portal
return 501 and the webhook runs in dev mode (raw JSON). Where Stripe is needed,
the module is monkeypatched with a stub.
"""
import os
import tempfile
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")

from fastapi.testclient import TestClient  # noqa: E402

import app.main  # noqa: E402,F401  (creates tables on the temp DB)
from app.core.db import SessionLocal  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.plans import PLANS, get_plan, enforce_page_cap, page_cap  # noqa: E402
from app.models import User, Website, CrawlJob, Subscription  # noqa: E402

client = TestClient(app.main.app)


def _register_user(email: str = "billing@test.com", password: str = "pw12345678"):
    res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert res.status_code == 201, res.text
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _user(email: str = "billing@test.com") -> User:
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()
    return user


def _seed_website(user_id: int, domain: str = "billingexample.com") -> int:
    db = SessionLocal()
    site = db.query(Website).filter(Website.user_id == user_id, Website.domain == domain).first()
    if site is None:
        site = Website(user_id=user_id, domain=domain, status="active")
        db.add(site)
        db.commit()
        db.refresh(site)
    site_id = site.id
    db.close()
    return site_id


def _seed_recent_job(website_id: int, minutes_ago: int = 5):
    db = SessionLocal()
    job = CrawlJob(
        website_id=website_id,
        status="completed",
        total_pages_scanned=1,
        total_issues_found=0,
        avg_score=80,
        started_at=datetime.utcnow() - timedelta(minutes=minutes_ago),
        finished_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.close()


class _FakeStripe:
    """Minimal in-memory stand-in for the stripe module."""

    def __init__(self):
        self.created_prices = {}
        self.session_url = "https://checkout.stripe.test/session_123"

    class Customer:
        @staticmethod
        def create(**kwargs):
            return type("C", (), {"id": "cus_test123"})()

    class Price:
        @staticmethod
        def create(**kwargs):
            plan = kwargs.get("metadata", {}).get("plan", "starter")
            return type("P", (), {"id": f"price_test_{plan}"})()

    class checkout:
        class Session:
            @staticmethod
            def create(**kwargs):
                return type("S", (), {"url": "https://checkout.stripe.test/session_123"})()

    class billing_portal:
        class Session:
            @staticmethod
            def create(**kwargs):
                return type("S", (), {"url": "https://billing.stripe.test/portal"})()


def test_plans_table():
    assert PLANS["free"].max_sites == 1
    assert PLANS["starter"].price_monthly_usd == 49
    assert PLANS["growth"].max_sites == 10
    assert PLANS["agency"].max_pages_per_scan == 100
    assert PLANS["agency"].scan_interval_hours == 2
    assert get_plan("unknown").id == "free"
    assert page_cap(_user() or type("U", (), {"plan": "free"})()) == 10


def test_page_cap_clamps():
    free_user = type("U", (), {"plan": "free"})()
    assert enforce_page_cap(free_user, 1000) == 10
    assert enforce_page_cap(free_user, None) == 10
    assert enforce_page_cap(free_user, 5) == 5
    agency_user = type("U", (), {"plan": "agency"})()
    assert enforce_page_cap(agency_user, 1000) == 100


def test_billing_status_free_plan():
    headers = _register_user()
    res = client.get("/api/v1/billing/status", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["plan"] == "free"
    assert data["max_sites"] == 1
    assert data["can_add_site"] is True
    assert data["billing_configured"] is False
    assert data["subscription_status"] == "none"
    assert set(data["plans"].keys()) == {"free", "starter", "growth", "agency"}


def test_site_limit_enforced_on_free_plan(monkeypatch):
    headers = _register_user("limit@test.com")
    user = _user("limit@test.com")

    # Stub the crawler so creating a site doesn't hit the network
    calls = []
    monkeypatch.setattr("app.api.website.run_website_crawl", lambda *a, **k: calls.append((a, k)))

    res = client.post("/api/v1/website", json={"domain": "sitelimit-one.com"}, headers=headers)
    assert res.status_code == 201

    res = client.post("/api/v1/website", json={"domain": "sitelimit-two.com"}, headers=headers)
    assert res.status_code == 402
    assert "Plan limit reached" in res.json()["detail"]

    db = SessionLocal()
    count = db.query(Website).filter(Website.user_id == user.id).count()
    db.close()
    assert count == 1


def test_scan_frequency_enforced_on_free_plan(monkeypatch):
    headers = _register_user("freq@test.com")
    user = _user("freq@test.com")
    site_id = _seed_website(user.id, "freqexample.com")
    _seed_recent_job(site_id, minutes_ago=5)  # free plan allows 1 scan / 24h

    monkeypatch.setattr("app.api.scan.run_website_crawl", lambda *a, **k: None)
    res = client.post("/api/v1/scan", json={"website_id": site_id}, headers=headers)
    assert res.status_code == 429
    assert "rate limit" in res.json()["detail"]["message"].lower()


def test_scan_allowed_after_interval(monkeypatch):
    headers = _register_user("freqok@test.com")
    user = _user("freqok@test.com")
    site_id = _seed_website(user.id, "freqokexample.com")
    _seed_recent_job(site_id, minutes_ago=25 * 60)  # 25h ago — over the 24h free interval

    calls = []
    monkeypatch.setattr("app.api.scan.run_website_crawl", lambda *a, **k: calls.append((a, k)))
    res = client.post("/api/v1/scan", json={"website_id": site_id}, headers=headers)
    assert res.status_code == 200
    assert len(calls) == 1
    # page cap passed to the crawler is clamped to the free plan cap (10)
    assert calls[0][1]["max_pages"] == 10


def test_checkout_returns_501_without_stripe():
    headers = _register_user("noconfig@test.com")
    res = client.post("/api/v1/billing/checkout", json={"plan": "starter"}, headers=headers)
    assert res.status_code == 501
    assert "not configured" in res.json()["detail"].lower()


def test_checkout_creates_session(monkeypatch):
    headers = _register_user("checkout@test.com")
    fake = _FakeStripe()
    monkeypatch.setattr("app.api.billing.stripe", fake)
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_xyz")

    res = client.post("/api/v1/billing/checkout", json={"plan": "growth"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["url"] == fake.session_url

    # invalid plan rejected
    res = client.post("/api/v1/billing/checkout", json={"plan": "free"}, headers=headers)
    assert res.status_code == 400

    monkeypatch.undo()
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "")


def test_webhook_checkout_completed_upgrades_plan():
    headers = _register_user("webhook@test.com")
    user = _user("webhook@test.com")

    payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": str(user.id), "plan": "starter"},
                "client_reference_id": str(user.id),
                "customer": "cus_webhook",
                "subscription": "sub_webhook",
            }
        },
    }
    res = client.post("/api/v1/billing/webhook", json=payload)
    assert res.status_code == 200

    db = SessionLocal()
    user = db.query(User).filter(User.id == user.id).first()
    assert user.plan == "starter"
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    assert sub is not None
    assert sub.stripe_subscription_id == "sub_webhook"
    assert sub.status == "active"
    db.close()

    # status endpoint now reflects the paid plan
    res = client.get("/api/v1/billing/status", headers=headers)
    assert res.json()["plan"] == "starter"
    assert res.json()["max_sites"] == 3
    assert res.json()["subscription_status"] == "active"


def test_webhook_subscription_deleted_downgrades():
    headers = _register_user("downgrade@test.com")
    user = _user("downgrade@test.com")

    client.post("/api/v1/billing/webhook", json={
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"user_id": str(user.id), "plan": "agency"},
                            "customer": "cus_dn", "subscription": "sub_dn"}},
    })

    res = client.post("/api/v1/billing/webhook", json={
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_dn", "customer": "cus_dn"}},
    })
    assert res.status_code == 200

    db = SessionLocal()
    user = db.query(User).filter(User.id == user.id).first()
    assert user.plan == "free"
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    assert sub.status == "canceled"
    db.close()


def test_cron_scan_caps_pages_by_plan(monkeypatch):
    headers = _register_user("croncap@test.com")
    user = _user("croncap@test.com")
    site_id = _seed_website(user.id, "croncap.com")

    monkeypatch.setattr(settings, "CRON_SECRET", "cron-secret-test")
    calls = []
    monkeypatch.setattr("app.api.scan.run_website_crawl", lambda *a, **k: calls.append((a, k)))

    res = client.post(
        "/api/v1/scan/cron",
        json={"max_pages": 1000, "website_ids": [site_id]},
        headers={"Authorization": "Bearer cron-secret-test"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["scans_started"] == 1
    assert data["max_pages"] == 1000  # requested value echoed
    # free plan cap applied to the actual crawl call
    assert calls[0][1]["max_pages"] == 10

    monkeypatch.undo()
    monkeypatch.setattr(settings, "CRON_SECRET", "")
