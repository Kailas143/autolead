from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    message = Column(Text, nullable=False)
    classification = Column(String)  # interested, not_interested, later, booked_call
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead")