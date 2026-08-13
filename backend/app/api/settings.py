from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsResponse(BaseModel):
    agency_name: Optional[str] = None
    semrush_api_key_set: bool = False
    ahrefs_api_key_set: bool = False

    class Config:
        from_attributes = True


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
        semrush_api_key_set=bool(current_user.semrush_api_key),
        ahrefs_api_key_set=bool(current_user.ahrefs_api_key),
    )
