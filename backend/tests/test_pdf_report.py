"""
Tests for the white-label PDF report export and the agency logo upload.

Hermetic: uses a temp SQLite DB, a tiny generated PNG logo, and pypdf to
extract text from the generated PDF (no external services).
"""
import base64
import io
import os
import struct
import tempfile
import zlib
from datetime import datetime

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")

from fastapi.testclient import TestClient  # noqa: E402

import app.main  # noqa: E402,F401  (creates tables on the temp DB)
from app.core.db import SessionLocal  # noqa: E402
from app.models import User, Website, CrawlJob, Page, SEOIssue, AISuggestion  # noqa: E402
from pypdf import PdfReader  # noqa: E402

client = TestClient(app.main.app)


def _make_png(w: int = 200, h: int = 60) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    row = b"\x00" + b"\x99\x66\xf1" * w
    idat = zlib.compress(row * h)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _register(email: str = "pdf@test.com"):
    client.post("/api/v1/auth/register", json={"email": email, "password": "pw12345678"})
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "pw12345678"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _seed_website(user_id: int) -> int:
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    website = db.query(Website).filter(Website.user_id == user_id, Website.domain == "pdfexample.com").first()
    if website is None:
        website = Website(user_id=user_id, domain="pdfexample.com", baseline_score=60, status="active")
        db.add(website)
        db.flush()

        job = CrawlJob(
            website_id=website.id, status="completed", total_pages_scanned=2,
            total_issues_found=1, avg_score=78, started_at=datetime.utcnow(),
        )
        db.add(job)
        db.flush()

        page = Page(
            website_id=website.id, url="https://pdfexample.com/", url_hash="b" * 64,
            title="Old Title", seo_score=78, word_count=400, missing_alt_count=1,
        )
        db.add(page)
        db.flush()

        issue = SEOIssue(
            page_id=page.id, issue_type="Missing Meta Description", severity="warning",
            description="Meta description missing", status="open",
        )
        db.add(issue)
        db.flush()

        db.add(AISuggestion(
            issue_id=issue.id, suggested_title="Optimized Title", status="approved",
            created_at=datetime.utcnow(),
        ))
        db.commit()
    website_id = website.id
    db.close()
    return website_id


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_pdf_requires_auth():
    res = client.get("/api/v1/reports/website/1/pdf")
    assert res.status_code == 401


def test_pdf_export_returns_whitelabel_pdf():
    headers = _register("pdf@test.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "pdf@test.com").first()
    user.agency_name = "Kathmandu SEO Agency"
    db.commit()
    website_id = _seed_website(user.id)
    db.close()

    res = client.get(f"/api/v1/reports/website/{website_id}/pdf", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/pdf")
    assert "attachment" in res.headers["content-disposition"]
    body = res.content
    assert body[:5] == b"%PDF-"

    text = _extract_text(body)
    assert "Kathmandu SEO Agency" in text, "agency name should appear in the PDF"
    assert "pdfexample.com" in text, "site domain should appear in the PDF"
    assert "SEO Performance Report" in text
    assert "Google Search Console" in text
    assert "Fixes Deployed" in text
    assert "Optimized Title" in text, "deployed fix should appear in the PDF"


def test_pdf_denies_other_users():
    _, website_id = _register_and_seed_other()
    headers = _register("pdf2@test.com")
    res = client.get(f"/api/v1/reports/website/{website_id}/pdf", headers=headers)
    assert res.status_code == 404


def _register_and_seed_other():
    headers = _register("pdfowner@test.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "pdfowner@test.com").first()
    website_id = _seed_website(user.id)
    db.close()
    return headers, website_id


def test_logo_upload_and_pdf_generation():
    headers = _register("logo@test.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "logo@test.com").first()
    user.agency_name = "Logo Agency"
    db.commit()
    website_id = _seed_website(user.id)
    db.close()

    png = _make_png()
    res = client.post(
        "/api/v1/settings/logo",
        files={"file": ("logo.png", png, "image/png")},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["logo_set"] is True

    # PDF generates fine with a logo attached
    res = client.get(f"/api/v1/reports/website/{website_id}/pdf", headers=headers)
    assert res.status_code == 200
    assert res.content[:5] == b"%PDF-"
    assert "Logo Agency" in _extract_text(res.content)

    # delete the logo
    res = client.delete("/api/v1/settings/logo", headers=headers)
    assert res.status_code == 200
    assert res.json()["logo_set"] is False


def test_logo_upload_rejects_non_image():
    headers = _register("badlogo@test.com")
    res = client.post(
        "/api/v1/settings/logo",
        files={"file": ("logo.txt", b"not an image", "text/plain")},
        headers=headers,
    )
    assert res.status_code == 400
    assert "PNG" in res.json()["detail"]
