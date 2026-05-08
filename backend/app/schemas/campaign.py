from typing import List, Optional

from pydantic import BaseModel


class SequenceBase(BaseModel):
    step_number: int
    subject: str
    body: str
    delay_days: int = 0


class SequenceCreate(SequenceBase):
    pass


class Sequence(SequenceBase):
    id: int
    campaign_id: int

    class Config:
        from_attributes = True


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    target_industry: Optional[str] = None


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