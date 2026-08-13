from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User, Website, Page, SEOIssue, AISuggestion, FixVersion
from app.schemas.issue import SEOIssueResponse, ApproveSuggestionRequest
from app.api.auth import get_current_user

router = APIRouter(prefix="/issues", tags=["Issues"])


class BulkApproveRequest(BaseModel):
    suggestion_ids: List[int]


@router.get("", response_model=List[SEOIssueResponse])
def get_website_issues(
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

    issues = db.query(SEOIssue).join(Page).filter(
        Page.website_id == website_id,
        SEOIssue.status.in_(["open", "resolved"])
    ).order_by(SEOIssue.created_at.desc()).all()

    res = []
    for issue in issues:
        item = SEOIssueResponse.model_validate(issue)
        item.page_url = issue.page.url if issue.page else None
        res.append(item)
    return res


@router.patch("/suggestion/{suggestion_id}")
def update_suggestion_status(
    suggestion_id: int,
    req: ApproveSuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    suggestion = db.query(AISuggestion).join(SEOIssue).join(Page).join(Website).filter(
        AISuggestion.id == suggestion_id,
        Website.user_id == current_user.id
    ).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if req.action not in ["approve", "reject", "update"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve', 'reject', or 'update'")

    if req.action == "approve":
        suggestion.status = "approved"
        if suggestion.issue:
            suggestion.issue.status = "resolved"
            
            # Save FixVersion snapshot for 1-click rollback
            version = FixVersion(
                website_id=suggestion.issue.page.website_id,
                issue_id=suggestion.issue.id,
                version_number=1,
                old_title=suggestion.issue.page.title,
                old_meta=suggestion.issue.page.meta_description,
                old_h1=suggestion.issue.page.h1,
                new_title=suggestion.suggested_title or suggestion.issue.page.title,
                new_meta=suggestion.suggested_meta or suggestion.issue.page.meta_description,
                new_h1=suggestion.suggested_h1 or suggestion.issue.page.h1,
                status="deployed"
            )
            db.add(version)

    elif req.action == "reject":
        suggestion.status = "rejected"
        if suggestion.issue:
            suggestion.issue.status = "open"

    # Apply text edits if provided
    if req.suggested_title is not None:
        suggestion.suggested_title = req.suggested_title
    if req.suggested_meta is not None:
        suggestion.suggested_meta = req.suggested_meta
    if req.suggested_h1 is not None:
        suggestion.suggested_h1 = req.suggested_h1

    db.commit()
    db.refresh(suggestion)
    return {"status": "success", "suggestion_id": suggestion_id, "new_status": suggestion.status}


@router.post("/bulk-approve")
def bulk_approve_suggestions(
    req: BulkApproveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk approve multiple AI suggestions in 1 transaction.
    """
    suggestions = db.query(AISuggestion).join(SEOIssue).join(Page).join(Website).filter(
        AISuggestion.id.in_(req.suggestion_ids),
        Website.user_id == current_user.id
    ).all()

    approved_count = 0
    for sug in suggestions:
        sug.status = "approved"
        if sug.issue:
            sug.issue.status = "resolved"
            version = FixVersion(
                website_id=sug.issue.page.website_id,
                issue_id=sug.issue.id,
                version_number=1,
                old_title=sug.issue.page.title,
                old_meta=sug.issue.page.meta_description,
                old_h1=sug.issue.page.h1,
                new_title=sug.suggested_title or sug.issue.page.title,
                new_meta=sug.suggested_meta or sug.issue.page.meta_description,
                new_h1=sug.suggested_h1 or sug.issue.page.h1,
                status="deployed"
            )
            db.add(version)
            approved_count += 1

    db.commit()
    return {"status": "success", "approved_count": approved_count}


@router.post("/revert/{suggestion_id}")
def revert_approved_fix(
    suggestion_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    1-Click Revert/Rollback deployed fix back to previous state.
    """
    suggestion = db.query(AISuggestion).join(SEOIssue).join(Page).join(Website).filter(
        AISuggestion.id == suggestion_id,
        Website.user_id == current_user.id
    ).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion.status = "pending"
    if suggestion.issue:
        suggestion.issue.status = "open"

    db.commit()
    return {"status": "success", "reverted_suggestion_id": suggestion_id}
