from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.db import Base


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    issue_id = Column(Integer, ForeignKey("seo_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    suggested_title = Column(Text, nullable=True)
    suggested_meta = Column(Text, nullable=True)
    suggested_h1 = Column(Text, nullable=True)
    suggested_h2_snippet = Column(Text, nullable=True)
    suggested_schema = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    issue = relationship("SEOIssue", back_populates="suggestions")
