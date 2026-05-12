from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    sequence_id = Column(Integer, ForeignKey("sequences.id"), nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    resend_id = Column(String, index=True, nullable=True)
    sent_at = Column(DateTime(timezone=True))
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    replied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())