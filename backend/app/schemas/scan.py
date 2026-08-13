from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ScanStartRequest(BaseModel):
    website_id: int


class ScanJobResponse(BaseModel):
    id: int
    website_id: int
    status: str
    total_pages_scanned: int
    total_issues_found: int
    error_message: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PageResponse(BaseModel):
    id: int
    website_id: int
    url: str
    status_code: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    canonical: Optional[str] = None
    robots: Optional[str] = None
    schema_type: Optional[str] = None
    word_count: int
    images_count: int
    missing_alt_count: int
    seo_score: int
    last_crawled_at: datetime

    class Config:
        from_attributes = True
