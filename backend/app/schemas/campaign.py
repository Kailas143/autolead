from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SequenceBase(BaseModel):
    step_number: int
    subject: str
    body: str
    delay_days: int = 0
    delay_minutes: int = 0
    mediatype: Optional[str] = None
    mimetype: Optional[str] = None
    media: Optional[str] = None
    caption: Optional[str] = None
    poll_question: Optional[str] = None
    poll_options: Optional[List[str]] = None


class SequenceCreate(SequenceBase):
    pass


class Sequence(SequenceBase):
    id: int
    campaign_id: int

    class Config:
        from_attributes = True


class CampaignSendRequest(BaseModel):
    sequence_id: int
    instance_name: Optional[str] = None


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    channel: Optional[str] = "email"
    evolution_instance_name: Optional[str] = None
    target_industry: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    daily_send_limit: int = 50
    send_window_start_hour: int = 9
    send_window_end_hour: int = 17


class CampaignCreate(CampaignBase):
    sequences: List[SequenceCreate] = []


class CampaignUpdate(CampaignBase):
    status: Optional[str] = None


class Campaign(CampaignBase):
    id: int
    status: str
    user_id: int
    sequences: List[Sequence] = []

    class Config:
        from_attributes = True
