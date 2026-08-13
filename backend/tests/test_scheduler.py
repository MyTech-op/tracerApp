"""
Tests for the automated daily scan scheduler that keeps reporting trends populated.
"""
import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")

from app.worker.celery import celery_app  # noqa: E402


def test_beat_schedule_configured():
    assert "daily-scheduled-seo-scans" in celery_app.conf.beat_schedule
    entry = celery_app.conf.beat_schedule["daily-scheduled-seo-scans"]
    assert entry["task"] == "run_scheduled_website_scans"


def test_scheduled_scan_task_registered():
    from app.worker.tasks import run_scheduled_website_scans  # noqa: F401
    assert "run_scheduled_website_scans" in celery_app.tasks
