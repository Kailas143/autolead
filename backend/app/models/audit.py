from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String) # INFO, ERROR, WARNING
    category = Column(String) # AI, EMAIL, CAMPAIGN, SYSTEM
    message = Column(Text)
    details = Column(JSON, nullable=True) # Stack trace or extra info
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AIUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_name = Column(String)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    task_type = Column(String) # generation, cleaning, classification
    created_at = Column(DateTime(timezone=True), server_default=func.now())
