from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True, index=True, default=None)
    stripe_subscription_id = Column(String(255), nullable=True, index=True, default=None)
    stripe_price_id = Column(String(255), nullable=True, default=None)
    plan = Column(String(50), default="free", nullable=False)  # starter, growth, agency
    status = Column(String(50), default="inactive", nullable=False)  # active, trialing, past_due, canceled, incomplete, inactive
    current_period_end = Column(DateTime, nullable=True, default=None)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="subscription")
