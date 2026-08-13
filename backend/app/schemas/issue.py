from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AISuggestionResponse(BaseModel):
    id: int
    issue_id: int
    suggested_title: Optional[str] = None
    suggested_meta: Optional[str] = None
    suggested_h1: Optional[str] = None
    suggested_h2_snippet: Optional[str] = None
    suggested_schema: Optional[dict] = None
    reasoning: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SEOIssueResponse(BaseModel):
    id: int
    page_id: int
    issue_type: str
    severity: str
    description: str
    status: str
    created_at: datetime
    page_url: Optional[str] = None
    suggestions: List[AISuggestionResponse] = []

    class Config:
        from_attributes = True


class ApproveSuggestionRequest(BaseModel):
    action: str  # "approve", "reject", or "update"
    suggested_title: Optional[str] = None
    suggested_meta: Optional[str] = None
    suggested_h1: Optional[str] = None
    suggested_h2_snippet: Optional[str] = None

