from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="active", nullable=False)  # active, scanning, error
    detected_industry = Column(String(100), nullable=True, default=None)
    baseline_score = Column(Integer, nullable=True, default=None)
    last_scan_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="websites")
    pages = relationship("Page", back_populates="website", cascade="all, delete-orphan")
    crawl_jobs = relationship("CrawlJob", back_populates="website", cascade="all, delete-orphan")

