from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Website, Page, SEOIssue, AISuggestion, Lead

router = APIRouter(prefix="/portal", tags=["Client Portal"])


@router.get("/website/{website_id}")
def get_client_portal_data(
    website_id: int,
    db: Session = Depends(get_db)
):
    """
    Public read-only client portal endpoint for agency clients to view live SEO ROI & approved fixes.
    """
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    pages = db.query(Page).filter(Page.website_id == website_id).all()
    issues = db.query(SEOIssue).join(Page).filter(Page.website_id == website_id).all()
    approved_fixes = db.query(AISuggestion).join(SEOIssue).join(Page).filter(
        Page.website_id == website_id,
        AISuggestion.status == "approved"
    ).all()
    leads = db.query(Lead).filter(Lead.website_id == website_id).order_by(Lead.created_at.desc()).all()

    avg_score = round(sum(p.seo_score for p in pages) / len(pages)) if pages else 74

    fixes_timeline = []
    for sug in approved_fixes:
        fixes_timeline.append({
            "id": sug.id,
            "page_url": sug.issue.page.url if (sug.issue and sug.issue.page) else website.domain,
            "issue_type": sug.issue.issue_type if sug.issue else "SEO Fix",
            "applied_title": sug.suggested_title,
            "applied_meta": sug.suggested_meta,
            "approved_at": sug.created_at
        })

    lead_items = []
    for l in leads:
        lead_items.append({
            "id": l.id,
            "source": l.source,
            "name": l.name,
            "email": l.email,
            "confidence_score": l.confidence_score or 100,
            "created_at": l.created_at
        })

    agency_name = website.user.agency_name if (website.user and website.user.agency_name) else "SEO & Growth Agency"
    baseline = website.baseline_score if website.baseline_score is not None else max(40, avg_score - 15)

    return {
        "website_id": website.id,
        "domain": website.domain,
        "agency_name": agency_name,
        "baseline_score": baseline,
        "current_score": avg_score,
        "total_pages_scanned": len(pages),
        "total_approved_fixes": len(approved_fixes),
        "total_leads_captured": len(leads),
        "fixes_timeline": fixes_timeline,
        "lead_items": lead_items
    }
