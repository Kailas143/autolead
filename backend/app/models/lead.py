from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Making it nullable for now to avoid migration issues with existing data
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    whatsapp_status = Column(String, nullable=False, default="unknown")
    company = Column(String)
    title = Column(String)
    linkedin_url = Column(String)
    website = Column(String)
    industry = Column(String)
    store_name = Column(String)
    city_area = Column(String)
    address = Column(String)
    notes = Column(Text)
    status = Column(String, default="new")  # new, contacted, replied, converted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
