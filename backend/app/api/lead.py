from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User, Website, Lead
from app.schemas.lead import LeadCaptureRequest, LeadResponse, LeadSummaryResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/lead", tags=["Leads & Conversions"])


@router.post("/capture", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def capture_lead(
    req: LeadCaptureRequest,
    db: Session = Depends(get_db)
):
    """
    Public CORS-enabled endpoint for form submissions and tracking snippet events from client websites.
    """
    website = db.query(Website).filter(Website.id == req.website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Confidence Score: 100% for explicit HTTP Referrer / direct AI domain, 85% for organic prompt UTMs
    conf_score = req.confidence_score or (100 if req.source in ["chatgpt", "perplexity", "claude", "google_organic"] else 85)

    lead = Lead(
        website_id=req.website_id,
        name=req.name or "Anonymous Lead",
        email=req.email,
        phone=req.phone,
        message=req.message,
        source=req.source or "google_organic",
        utm_source=req.utm_source,
        utm_medium=req.utm_medium,
        utm_campaign=req.utm_campaign,
        page_url=req.page_url or f"https://{website.domain}",
        confidence_score=conf_score,
        created_at=datetime.utcnow()
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("", response_model=List[LeadResponse])
def get_website_leads(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated endpoint retrieving all captured leads for a website.
    """
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    return db.query(Lead).filter(
        Lead.website_id == website_id
    ).order_by(Lead.created_at.desc()).all()


@router.post("/seed/{website_id}", response_model=List[LeadResponse])
def seed_sample_leads(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Seed realistic sample inquiry leads for demonstration & client pitch.
    """
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    ind = (website.detected_industry or "Services").lower()
    
    if "e-commerce" in ind or "retail" in ind:
        sample_data = [
            {
                "name": "Sarah Jenkins", "email": "sarah.j@gmail.com", "phone": "+1 (555) 234-8901",
                "message": f"Interested in bulk order pricing on {website.domain}. Please send custom catalog.",
                "source": "chatgpt", "utm_source": "chatgpt_recommendation", "utm_medium": "ai_search", "utm_campaign": "products_ai",
                "page_url": f"https://{website.domain}/products", "days_ago": 0
            },
            {
                "name": "David Miller", "email": "david.m@corp.com", "phone": "+44 7700 900123",
                "message": f"Inquiring about corporate account discount and expedited shipping details.",
                "source": "google_organic", "utm_source": "google", "utm_medium": "organic", "utm_campaign": "search_brand",
                "page_url": f"https://{website.domain}/pricing", "days_ago": 1
            }
        ]
    else:
        sample_data = [
            {
                "name": "Sarah Jenkins", "email": "sarah.j@gmail.com", "phone": "+1 (555) 234-8901",
                "message": f"Found {website.domain} via ChatGPT recommendation. Seeking consultation quote for your services.",
                "source": "chatgpt", "utm_source": "chatgpt_recommendation", "utm_medium": "ai_search", "utm_campaign": "services_ai",
                "page_url": f"https://{website.domain}/services", "days_ago": 0
            },
            {
                "name": "David Miller", "email": "david.m@techcorp.com", "phone": "+44 7700 900123",
                "message": f"Inquiring about service packages & pricing options for our team.",
                "source": "google_organic", "utm_source": "google", "utm_medium": "organic", "utm_campaign": "seo_search",
                "page_url": f"https://{website.domain}/pricing", "days_ago": 1
            },
            {
                "name": "Elena Rostova", "email": "elena.r@business.de", "phone": "+49 151 5550123",
                "message": f"Clicked contact link on {website.domain}. Interested in custom implementation.",
                "source": "whatsapp_click", "utm_source": "whatsapp", "utm_medium": "chat_cta", "utm_campaign": "direct_chat",
                "page_url": f"https://{website.domain}/contact", "days_ago": 2
            },
            {
                "name": "Michael Chen", "email": "m.chen@venture.sg", "phone": "+65 9123 4567",
                "message": f"Found site on Perplexity AI search. Looking for enterprise solutions.",
                "source": "perplexity", "utm_source": "perplexity_ai", "utm_medium": "geo_search", "utm_campaign": "ai_geo",
                "page_url": f"https://{website.domain}/about", "days_ago": 3
            }
        ]

    created_leads = []
    for item in sample_data:
        c_score = 100 if item["source"] in ["chatgpt", "perplexity", "google_organic"] else 85
        lead = Lead(
            website_id=website_id,
            name=item["name"],
            email=item["email"],
            phone=item["phone"],
            message=item["message"],
            source=item["source"],
            utm_source=item["utm_source"],
            utm_medium=item["utm_medium"],
            utm_campaign=item["utm_campaign"],
            page_url=item["page_url"],
            confidence_score=c_score,
            created_at=datetime.utcnow() - timedelta(days=item["days_ago"])
        )
        db.add(lead)
        created_leads.append(lead)

    db.commit()
    for l in created_leads:
        db.refresh(l)

    return created_leads
