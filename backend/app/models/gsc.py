from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.db import Base


class SearchConsoleProfile(Base):
    """OAuth credentials + sync state for a website's Google Search Console property."""
    __tablename__ = "search_console_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    # GSC property URL, e.g. "sc-domain:example.com" or "https://example.com/"
    site_url = Column(String(255), nullable=True)
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="connected", nullable=False)  # connected, error
    error_message = Column(Text, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    website = relationship("Website", backref="search_console_profile", uselist=False)


class GSCMetric(Base):
    """Daily site-level Search Analytics aggregate (clicks, impressions, CTR, avg position)."""
    __tablename__ = "gsc_metrics"
    __table_args__ = (UniqueConstraint("website_id", "date", name="uq_gsc_metrics_website_date"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    position = Column(Float, default=0.0)


class GSCQueryMetric(Base):
    """Top search queries snapshot per sync day (bounded to keep storage sane)."""
    __tablename__ = "gsc_query_metrics"
    __table_args__ = (UniqueConstraint("website_id", "date", "query", name="uq_gsc_queries_website_date_query"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    query = Column(String(255), nullable=False)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    position = Column(Float, default=0.0)
