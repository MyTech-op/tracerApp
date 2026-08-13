import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User, Website, CrawlJob
from app.schemas.scan import ScanStartRequest, ScanJobResponse
from app.api.auth import get_current_user
from app.core.config import settings
from app.core.plans import scan_allowed, enforce_page_cap, last_scan_at, get_plan
from app.worker.tasks import run_website_crawl

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["Scans"])


class CronScanOptions(BaseModel):
    max_pages: Optional[int] = 15
    website_ids: Optional[List[int]] = None


@router.post("", response_model=ScanJobResponse)
def start_website_scan(
    req: ScanStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    website = db.query(Website).filter(
        Website.id == req.website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    allowed, next_at = scan_allowed(db, current_user, website.id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Scan rate limit reached for your plan",
                "next_allowed_at": next_at.isoformat() if next_at else None,
                "upgrade_hint": "Upgrade at /billing to scan more frequently",
            },
        )

    job = CrawlJob(
        website_id=website.id,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Trigger async Celery task (or synchronous fallback if Celery not active)
    max_pages = enforce_page_cap(current_user, None)
    try:
        run_website_crawl.delay(job.id, website.id, max_pages=max_pages)
    except Exception:
        # Synchronous execution fallback for quick testing
        run_website_crawl(job.id, website.id, max_pages=max_pages)

    db.refresh(job)
    return job


@router.get("/status/{job_id}", response_model=ScanJobResponse)
def get_scan_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(CrawlJob).join(Website).filter(
        CrawlJob.id == job_id,
        Website.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    return job


@router.api_route("/cron", methods=["GET", "POST"])
def run_scheduled_cron_scan(
    options: Optional[CronScanOptions] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Cron-triggered scan entrypoint for serverless hosts (Vercel Cron).

    Runs crawls inline (no Celery worker needed) for every tracked website that
    is not currently scanning. Guarded by `CRON_SECRET`; disabled when it is
    not set, so an unauthenticated cron can never trigger scans.
    """
    if not settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Cron scanning is disabled (CRON_SECRET not set)")

    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {settings.CRON_SECRET}":
        raise HTTPException(status_code=401, detail="Invalid cron secret")

    max_pages = (options.max_pages if options else None) or 15
    website_ids = options.website_ids if options else None

    query = db.query(Website).filter(Website.status != "scanning")
    if website_ids:
        query = query.filter(Website.id.in_(website_ids))
    websites = query.all()

    started = 0
    failed = 0
    skipped_frequency = 0
    for website in websites:
        try:
            owner = db.query(User).filter(User.id == website.user_id).first()
            if owner is None:
                continue
            plan = get_plan(owner.plan)
            last = last_scan_at(db, website.id)
            if last is not None:
                if datetime.utcnow() < last + timedelta(hours=plan.scan_interval_hours):
                    skipped_frequency += 1
                    continue

            job = CrawlJob(website_id=website.id, status="pending")
            db.add(job)
            db.commit()
            db.refresh(job)

            run_website_crawl(job.id, website.id, max_pages=enforce_page_cap(owner, max_pages))
            started += 1
        except Exception as e:
            logger.warning(f"Cron scan failed for website {website.id}: {str(e)}")
            failed += 1
            db.rollback()

    return {
        "status": "completed",
        "scans_started": started,
        "failed": failed,
        "skipped_frequency": skipped_frequency,
        "max_pages": max_pages,
    }


@router.get("/history/{website_id}", response_model=List[ScanJobResponse])
def get_website_scan_history(
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

    return db.query(CrawlJob).filter(
        CrawlJob.website_id == website_id
    ).order_by(CrawlJob.started_at.desc()).all()
