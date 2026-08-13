from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    message = Column(Text, nullable=True)
    
    # Traffic Source (chatgpt, perplexity, claude, google_organic, direct, whatsapp_click, phone_call)
    source = Column(String(100), default="google_organic")
    
    # UTM Parameters
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    
    page_url = Column(String(500), nullable=True)
    confidence_score = Column(Integer, default=100)  # 100 for verified HTTP referrer, 85 for organic prompt UTM
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    website = relationship("Website", backref="leads")
