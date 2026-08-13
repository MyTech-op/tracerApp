from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.db import Base


class PageSnapshot(Base):
    __tablename__ = "page_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_hash = Column(String(64), nullable=False)
    raw_seo_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    page = relationship("Page", back_populates="snapshots")


class PageChange(Base):
    __tablename__ = "page_changes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_snapshot_id = Column(Integer, ForeignKey("page_snapshots.id", ondelete="SET NULL"), nullable=True)
    current_snapshot_id = Column(Integer, ForeignKey("page_snapshots.id", ondelete="SET NULL"), nullable=True)
    diff_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    page = relationship("Page", back_populates="changes")
