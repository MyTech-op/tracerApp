from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LeadCaptureRequest(BaseModel):
    website_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = "google_organic"
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    page_url: Optional[str] = None
    confidence_score: Optional[int] = 100


class LeadResponse(BaseModel):
    id: int
    website_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    source: str
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    page_url: Optional[str] = None
    confidence_score: int = 100
    created_at: datetime

    class Config:
        from_attributes = True


class LeadSummaryResponse(BaseModel):
    total_leads: int
    ai_search_leads: int
    google_organic_leads: int
    direct_whatsapp_leads: int
