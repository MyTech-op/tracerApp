from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User, SEOIssue, AISuggestion, Page, Website
from app.schemas.issue import AISuggestionResponse
from app.api.auth import get_current_user
from app.ai.factory import get_ai_provider

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/generate-fix/{issue_id}", response_model=AISuggestionResponse)
def generate_fix_for_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    issue = db.query(SEOIssue).join(Page).join(Website).filter(
        SEOIssue.id == issue_id,
        Website.user_id == current_user.id
    ).first()

    if not issue or not issue.page:
        raise HTTPException(status_code=404, detail="Issue or page not found")

    provider = get_ai_provider()
    ai_res = provider.generate_seo_fix(
        issue_type=issue.issue_type,
        page_title=issue.page.title,
        h1=issue.page.h1,
        body_sample=issue.page.meta_description
    )

    suggestion = AISuggestion(
        issue_id=issue.id,
        suggested_title=ai_res.get("suggested_title"),
        suggested_meta=ai_res.get("suggested_meta"),
        suggested_h1=ai_res.get("suggested_h1"),
        suggested_h2_snippet=ai_res.get("suggested_h2_snippet"),
        reasoning=ai_res.get("reasoning"),
        status="pending"
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)

    return suggestion
