import base64
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsResponse(BaseModel):
    agency_name: Optional[str] = None
    logo_set: bool = False
    semrush_api_key_set: bool = False
    ahrefs_api_key_set: bool = False

    class Config:
        from_attributes = True


MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MB
ALLOWED_LOGO_TYPES = {"image/png": "png", "image/jpeg": "jpeg", "image/webp": "webp"}


class SettingsUpdateRequest(BaseModel):
    agency_name: Optional[str] = None
    semrush_api_key: Optional[str] = None
    ahrefs_api_key: Optional[str] = None


@router.get("", response_model=SettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
):
    return SettingsResponse(
        agency_name=current_user.agency_name,
        logo_set=bool(current_user.logo),
        semrush_api_key_set=bool(current_user.semrush_api_key),
        ahrefs_api_key_set=bool(current_user.ahrefs_api_key),
    )


@router.post("/logo", response_model=SettingsResponse)
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload the agency logo used on white-label PDF reports (PNG/JPEG/WebP, max 2MB)."""
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_LOGO_TYPES:
        raise HTTPException(status_code=400, detail="Logo must be a PNG, JPEG, or WebP image")

    data = await file.read()
    if len(data) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=400, detail="Logo too large - maximum 2 MB")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    ext = ALLOWED_LOGO_TYPES[content_type]
    current_user.logo = f"data:{content_type};base64,{base64.b64encode(data).decode('ascii')}"
    db.commit()

    return SettingsResponse(
        agency_name=current_user.agency_name,
        logo_set=True,
        semrush_api_key_set=bool(current_user.semrush_api_key),
        ahrefs_api_key_set=bool(current_user.ahrefs_api_key),
    )


@router.delete("/logo", response_model=SettingsResponse)
def delete_logo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.logo = None
    db.commit()
    return SettingsResponse(
        agency_name=current_user.agency_name,
        logo_set=False,
        semrush_api_key_set=bool(current_user.semrush_api_key),
        ahrefs_api_key_set=bool(current_user.ahrefs_api_key),
    )


@router.patch("", response_model=SettingsResponse)
def update_settings(
    req: SettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.agency_name is not None:
        current_user.agency_name = req.agency_name
    if req.semrush_api_key is not None:
        current_user.semrush_api_key = req.semrush_api_key if req.semrush_api_key.strip() else None
    if req.ahrefs_api_key is not None:
        current_user.ahrefs_api_key = req.ahrefs_api_key if req.ahrefs_api_key.strip() else None

    db.commit()
    db.refresh(current_user)

    return SettingsResponse(
        agency_name=current_user.agency_name,
        logo_set=bool(current_user.logo),
        semrush_api_key_set=bool(current_user.semrush_api_key),
        ahrefs_api_key_set=bool(current_user.ahrefs_api_key),
    )
