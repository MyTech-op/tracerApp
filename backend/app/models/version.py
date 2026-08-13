from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class FixVersion(Base):
    __tablename__ = "fix_versions"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False)
    issue_id = Column(Integer, ForeignKey("seo_issues.id", ondelete="CASCADE"), nullable=False)
    
    version_number = Column(Integer, default=1)
    old_title = Column(Text, nullable=True)
    old_meta = Column(Text, nullable=True)
    old_h1 = Column(Text, nullable=True)
    
    new_title = Column(Text, nullable=True)
    new_meta = Column(Text, nullable=True)
    new_h1 = Column(Text, nullable=True)
    
    status = Column(String(50), default="deployed")  # deployed, reverted
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    issue = relationship("SEOIssue", backref="versions")
