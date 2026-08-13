from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User, Website, Page
from app.schemas.scan import PageResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/pages", tags=["Pages"])


@router.get("", response_model=List[PageResponse])
def get_website_pages(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    return db.query(Page).filter(Page.website_id == website_id).order_by(Page.seo_score.asc()).all()


@router.get("/{page_id}", response_model=PageResponse)
def get_page_detail(
    page_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    page = db.query(Page).join(Website).filter(
        Page.id == page_id,
        Website.user_id == current_user.id
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page
