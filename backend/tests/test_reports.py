"""
End-to-end tests for the reporting API.

Uses an isolated temp SQLite database so it never touches the local seoops.db.
Must set DATABASE_URL before importing the app.
"""
import os
import tempfile
from datetime import datetime

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.models import User, Website, CrawlJob, Page, SEOIssue, AISuggestion  # noqa: E402

client = TestClient(app)


def _seed_data():
    """Create a user, website, completed crawl job with avg_score, page, issue + approved fix."""
    db = SessionLocal()
    # Idempotent: reuse the user + website if a previous test already created them
    user = db.query(User).filter(User.email == "reporter@test.com").first()
    if user is None:
        user = User(email="reporter@test.com", password_hash="x", plan="free")
        db.add(user)
        db.flush()

    website = db.query(Website).filter(
        Website.user_id == user.id, Website.domain == "example.com"
    ).first()
    if website is None:
        website = Website(user_id=user.id, domain="example.com", baseline_score=60, status="active")
        db.add(website)
        db.flush()

    if db.query(CrawlJob).filter(CrawlJob.website_id == website.id).count() == 0:
        job = CrawlJob(
            website_id=website.id,
            status="completed",
            total_pages_scanned=2,
            total_issues_found=3,
            avg_score=78,
            started_at=datetime.utcnow(),
        )
        db.add(job)

        page = Page(
            website_id=website.id,
            url="https://example.com/",
            url_hash="a" * 64,
            title="Old Title",
            seo_score=78,
            word_count=400,
            missing_alt_count=1,
        )
        db.add(page)
        db.flush()

        issue = SEOIssue(
            page_id=page.id,
            issue_type="Missing Meta Description",
            severity="warning",
            description="Meta description missing",
            status="open",
        )
        db.add(issue)
        db.flush()

        db.add(AISuggestion(
            issue_id=issue.id,
            suggested_title="Optimized Title",
            suggested_meta="Optimized meta.",
            status="approved",
        ))

    db.commit()
    user_id = user.id
    website_id = website.id
    db.close()
    return user_id, website_id


def _user_id_by_email(email: str) -> int:
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()
    return user.id


def _auth_headers(user_id: int):
    return {"Authorization": f"Bearer {create_access_token(subject=user_id)}"}


def test_reports_overview():
    user_id, _ = _seed_data()
    headers = _auth_headers(user_id)
    res = client.get("/api/v1/reports/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["total_sites"] == 1
    assert data["summary"]["open_issues"] == 1
    assert data["summary"]["critical_issues"] == 0
    assert data["summary"]["warning_issues"] == 1
    assert data["summary"]["approved_fixes"] == 1
    assert data["summary"]["total_scans"] == 1
    assert data["sites"][0]["domain"] == "example.com"
    assert data["sites"][0]["current_score"] == 78
    assert data["sites"][0]["score_delta"] == 18


def test_reports_overview_requires_auth():
    res = client.get("/api/v1/reports/overview")
    assert res.status_code == 401


def test_website_report():
    user_id, website_id = _seed_data()
    headers = _auth_headers(user_id)
    res = client.get(f"/api/v1/reports/website/{website_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["domain"] == "example.com"
    assert data["baseline_score"] == 60
    assert data["current_score"] == 78
    assert len(data["score_history"]) == 1
    assert data["score_history"][0]["score"] == 78
    assert data["severity_breakdown"]["warning"] == 1
    assert data["issue_breakdown"][0]["issue_type"] == "Missing Meta Description"
    assert len(data["top_pages"]) == 1
    assert data["top_pages"][0]["seo_score"] == 78
    assert data["fixes_timeline"][0]["applied_title"] == "Optimized Title"


def test_website_report_denies_other_users():
    _, website_id = _seed_data()
    client.post("/api/v1/auth/register", json={"email": "other@test.com", "password": "pw12345678"})
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "other@test.com", "password": "pw12345678"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    res = client.get(f"/api/v1/reports/website/{website_id}", headers=headers)
    assert res.status_code == 404


def test_csv_export():
    user_id, website_id = _seed_data()
    headers = _auth_headers(user_id)
    res = client.get(f"/api/v1/reports/website/{website_id}/export", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    body = res.text
    assert "example.com" in body
    assert "Missing Meta Description" in body
    assert "Pages" in body and "Open Issues" in body
