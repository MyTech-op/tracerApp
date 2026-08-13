from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import settings
from app.core.security import verify_state
from app.models import User, Website, SearchConsoleProfile
from app.api.auth import get_current_user
from app.services import gsc as gsc_service

router = APIRouter(prefix="/gsc", tags=["Google Search Console"])


@router.get("/auth-url")
def get_gsc_auth_url(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate the Google OAuth consent URL for a tracked website."""
    website = db.query(Website).filter(
        Website.id == website_id, Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    if not settings.GSC_CLIENT_ID or not settings.GSC_CLIENT_SECRET:
        raise HTTPException(
            status_code=400,
            detail="Google Search Console is not configured. Set GSC_CLIENT_ID and GSC_CLIENT_SECRET.",
        )
    return {"url": gsc_service.build_auth_url(website_id)}


@router.get("/callback")
def gsc_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    OAuth redirect target. Verifies the signed state, exchanges the code,
    stores tokens, auto-picks the matching GSC property, then redirects back
    to the frontend report page.
    """
    website_id_str = verify_state(state)
    if website_id_str is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    website = db.query(Website).filter(Website.id == int(website_id_str)).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    try:
        result = gsc_service.connect_website(db, website, code)
        ok = result.get("status") in ("ok", "not_connected")
    except Exception as e:
        ok = False

    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/reports/{website.id}?gsc={'connected' if ok else 'error'}",
        status_code=302,
    )


@router.get("/status/{website_id}")
def get_gsc_status(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    website = db.query(Website).filter(
        Website.id == website_id, Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    profile = db.query(SearchConsoleProfile).filter(
        SearchConsoleProfile.website_id == website_id
    ).first()

    if not profile:
        return {"connected": False, "site_url": None, "last_sync_at": None,
                "status": "disconnected", "error_message": None}
    return {
        "connected": bool(profile.site_url),
        "site_url": profile.site_url,
        "last_sync_at": profile.last_sync_at.isoformat() + "Z" if profile.last_sync_at else None,
        "status": profile.status,
        "error_message": profile.error_message,
    }


@router.post("/sync/{website_id}")
def sync_gsc_now(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    website = db.query(Website).filter(
        Website.id == website_id, Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return gsc_service.sync_gsc_for_website(db, website)


@router.post("/disconnect/{website_id}")
def disconnect_gsc(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    website = db.query(Website).filter(
        Website.id == website_id, Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    profile = db.query(SearchConsoleProfile).filter(
        SearchConsoleProfile.website_id == website_id
    ).first()
    if profile:
        db.delete(profile)
        db.commit()
    return {"status": "disconnected"}


@router.api_route("/cron", methods=["GET", "POST"])
def gsc_cron_sync(
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Serverless-cron entrypoint (Vercel Cron): sync all connected GSC profiles."""
    if not settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Cron sync is disabled (CRON_SECRET not set)")
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {settings.CRON_SECRET}":
        raise HTTPException(status_code=401, detail="Invalid cron secret")

    return gsc_service.sync_all_gsc_profiles(db)
