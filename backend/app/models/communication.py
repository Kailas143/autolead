from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class Communication(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    sequence_id = Column(Integer, ForeignKey("sequences.id"), nullable=True)
    channel = Column(String, nullable=False, default="email")
    provider = Column(String, nullable=True)
    provider_id = Column(String, index=True, nullable=True)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="sent")
    sent_at = Column(DateTime(timezone=True))
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    replied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
