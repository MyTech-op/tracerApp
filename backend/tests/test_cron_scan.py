"""
Tests for the serverless cron-scan endpoint (Vercel Cron / scan/cron).
"""
import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402
from app.models import User, Website  # noqa: E402

client = TestClient(app)


def _seed_website(status: str = "active") -> int:
    db = SessionLocal()
    user = User(email="cron@test.com", password_hash="x", plan="free")
    db.add(user)
    db.flush()
    website = Website(user_id=user.id, domain="cron-example.com", status=status)
    db.add(website)
    db.commit()
    website_id = website.id
    db.close()
    return website_id


def test_cron_disabled_without_secret():
    old = settings.CRON_SECRET
    settings.CRON_SECRET = ""
    try:
        res = client.post("/api/v1/scan/cron")
        assert res.status_code == 403
    finally:
        settings.CRON_SECRET = old


def test_cron_rejects_wrong_secret():
    old = settings.CRON_SECRET
    settings.CRON_SECRET = "top-secret"
    try:
        res = client.post("/api/v1/scan/cron", headers={"Authorization": "Bearer wrong"})
        assert res.status_code == 401
    finally:
        settings.CRON_SECRET = old


def test_cron_runs_with_valid_secret_and_no_sites():
    old = settings.CRON_SECRET
    settings.CRON_SECRET = "top-secret"
    try:
        res = client.post(
            "/api/v1/scan/cron",
            headers={"Authorization": "Bearer top-secret"},
            json={"max_pages": 5},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["scans_started"] == 0
        assert data["max_pages"] == 5
    finally:
        settings.CRON_SECRET = old


def test_cron_skips_websites_currently_scanning():
    _seed_website(status="scanning")
    old = settings.CRON_SECRET
    settings.CRON_SECRET = "top-secret"
    try:
        res = client.post(
            "/api/v1/scan/cron",
            headers={"Authorization": "Bearer top-secret"},
        )
        assert res.status_code == 200
        # Scanning site is skipped, so no network crawl is triggered.
        assert res.json()["scans_started"] == 0
    finally:
        settings.CRON_SECRET = old
