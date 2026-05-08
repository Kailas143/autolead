from typing import Optional

from pydantic import BaseModel


class LeadBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(LeadBase):
    status: Optional[str] = None


class Lead(LeadBase):
    id: int
    status: str

    class Config:
        from_attributes = True