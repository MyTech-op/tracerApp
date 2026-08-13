from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.db import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    url_hash = Column(String(64), index=True, nullable=False)  # SHA-256 of canonical URL
    status_code = Column(Integer, default=200)
    title = Column(Text, nullable=True)
    meta_description = Column(Text, nullable=True)
    h1 = Column(Text, nullable=True)
    canonical = Column(Text, nullable=True)
    robots = Column(String(255), nullable=True)
    schema_type = Column(String(255), nullable=True)
    word_count = Column(Integer, default=0)
    images_count = Column(Integer, default=0)
    missing_alt_count = Column(Integer, default=0)
    internal_links_count = Column(Integer, default=0)
    external_links_count = Column(Integer, default=0)
    last_content_hash = Column(String(64), nullable=True)
    seo_score = Column(Integer, default=100)
    last_crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    website = relationship("Website", back_populates="pages")
    snapshots = relationship("PageSnapshot", back_populates="page", cascade="all, delete-orphan")
    changes = relationship("PageChange", back_populates="page", cascade="all, delete-orphan")
    issues = relationship("SEOIssue", back_populates="page", cascade="all, delete-orphan")
