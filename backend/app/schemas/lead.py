from typing import Optional, List

from pydantic import BaseModel


class LeadBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    whatsapp_status: Optional[str] = "unknown"
    store_name: Optional[str] = None
    city_area: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    whatsapp_status: Optional[str] = None
    store_name: Optional[str] = None
    city_area: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class Lead(LeadBase):
    id: int
    user_id: int
    status: str

    class Config:
        from_attributes = True


class WhatsAppSendRequest(BaseModel):
    message: Optional[str] = None
    instance_name: Optional[str] = None
    campaign_id: Optional[int] = None
    sequence_id: Optional[int] = None
    mediatype: Optional[str] = None
    mimetype: Optional[str] = None
    media: Optional[str] = None
    caption: Optional[str] = None


class WhatsAppBulkValidateRequest(BaseModel):
    lead_ids: List[int]
    instance_name: Optional[str] = None
