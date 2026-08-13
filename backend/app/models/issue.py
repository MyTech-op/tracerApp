from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class SEOIssue(Base):
    __tablename__ = "seo_issues"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_type = Column(String(100), nullable=False, index=True)  # Missing Title, Title Too Long, Missing Meta, etc.
    severity = Column(String(20), default="warning", nullable=False)  # critical, warning, info
    description = Column(Text, nullable=False)
    status = Column(String(20), default="open", nullable=False)  # open, resolved, ignored
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    page = relationship("Page", back_populates="issues")
    suggestions = relationship("AISuggestion", back_populates="issue", cascade="all, delete-orphan")
