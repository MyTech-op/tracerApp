from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.user import User
from app.models.website import Website
from app.schemas.website import WebsiteCreate, WebsiteResponse
from app.api.auth import get_current_user

from app.models import CrawlJob
from app.worker.tasks import run_website_crawl

router = APIRouter(prefix="/website", tags=["Websites"])


@router.post("", response_model=WebsiteResponse, status_code=status.HTTP_201_CREATED)
def create_website(
    website_in: WebsiteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_domain = website_in.domain.strip().lower()
    if clean_domain.startswith("https://"):
        clean_domain = clean_domain[8:]
    elif clean_domain.startswith("http://"):
        clean_domain = clean_domain[7:]
    if clean_domain.endswith("/"):
        clean_domain = clean_domain[:-1]

    existing = db.query(Website).filter(
        Website.user_id == current_user.id,
        Website.domain == clean_domain
    ).first()
    if existing:
        return existing

    website = Website(
        user_id=current_user.id,
        domain=clean_domain,
        status="scanning"
    )
    db.add(website)
    db.commit()
    db.refresh(website)

    # Auto-trigger initial crawl scan
    job = CrawlJob(
        website_id=website.id,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        run_website_crawl.delay(job.id, website.id)
    except Exception:
        # Fallback to direct synchronous execution if Celery background runner is offline
        run_website_crawl(job.id, website.id)

    db.refresh(website)
    return website


@router.get("", response_model=List[WebsiteResponse])
def list_websites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Website).filter(Website.user_id == current_user.id).all()


@router.delete("/{website_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_website(
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
    db.delete(website)
    db.commit()
    return None
