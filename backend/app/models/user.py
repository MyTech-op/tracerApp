from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import relationship
from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    plan = Column(String(50), default="free", nullable=False)  # free, starter, pro, agency
    agency_name = Column(String(255), nullable=True, default=None)
    logo = Column(Text().with_variant(MEDIUMTEXT, "mysql"), nullable=True, default=None)  # data URL: data:image/png;base64,...
    semrush_api_key = Column(Text, nullable=True, default=None)
    ahrefs_api_key = Column(Text, nullable=True, default=None)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    websites = relationship("Website", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")

