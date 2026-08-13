from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, crawling, parsing, completed, failed
    total_pages_scanned = Column(Integer, default=0)
    total_issues_found = Column(Integer, default=0)
    avg_score = Column(Integer, nullable=True)  # Average SEO health score captured at scan completion
    error_message = Column(String(255), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    website = relationship("Website", back_populates="crawl_jobs")
