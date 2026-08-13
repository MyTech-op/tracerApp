from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


class WebsiteCreate(BaseModel):
    domain: str


class WebsiteResponse(BaseModel):
    id: int
    user_id: int
    domain: str
    status: str
    last_scan_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
