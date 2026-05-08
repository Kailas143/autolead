from typing import Optional

from pydantic import BaseModel


class EmailBase(BaseModel):
    subject: str
    body: str


class EmailCreate(EmailBase):
    lead_id: int
    campaign_id: int
    sequence_id: int


class Email(EmailBase):
    id: int
    lead_id: int
    campaign_id: int
    sequence_id: int
    sent_at: Optional[str] = None
    opened: bool = False
    clicked: bool = False
    replied: bool = False

    class Config:
        from_attributes = True