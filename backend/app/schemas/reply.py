from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .lead import Lead


class ReplyBase(BaseModel):
    message: str
    classification: str


class ReplyCreate(ReplyBase):
    email_id: Optional[int] = None
    lead_id: int


class Reply(ReplyBase):
    id: int
    email_id: Optional[int] = None
    lead_id: int
    created_at: datetime
    lead: Optional[Lead] = None

    class Config:
        from_attributes = True
        populate_by_name = True