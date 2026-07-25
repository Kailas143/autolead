from typing import Any, List, Optional
from datetime import datetime, timezone
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app import schemas, models
from app.api import deps
from app.services.csv_service import csv_service
from app.services.email_service import email_service
from app.services.whatsapp_service import whatsapp_service
from app.models.communication import Communication
from app.utils.template_vars import replace_template_vars
from app.workers.tasks import process_csv_import

router = APIRouter()


def _whatsapp_status_for(phone: Optional[str], is_whatsapp: Optional[bool] = None) -> str:
    if not phone or not phone.strip():
        return "missing"
    if is_whatsapp is True:
        return "valid"
    if is_whatsapp is False:
        return "invalid"
    return "unknown"

@router.get("/", response_model=List[schemas.Lead])
def read_leads(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve leads belonging to the current user.
    """
    leads = db.query(models.Lead).filter(models.Lead.user_id == current_user.id).offset(skip).limit(limit).all()
    return leads

@router.post("/", response_model=schemas.Lead)
def create_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_in: schemas.LeadCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new lead manually.
    """
    lead_data = lead_in.dict(exclude={"whatsapp_status"})
    lead = models.Lead(
        **lead_data,
        user_id=current_user.id,
        status="new",
        whatsapp_status=_whatsapp_status_for(lead_in.phone),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def _render_whatsapp_body(template: str, lead: models.Lead) -> str:
    replacements = {
        "first_name": lead.first_name or "",
        "last_name": lead.last_name or "",
        "company": lead.company or "",
        "title": lead.title or "",
        "industry": lead.industry or "",
    }
    return replace_template_vars(template, replacements)


def _resolve_whatsapp_instance_name(current_user_id: int, explicit_instance_name: Optional[str] = None, campaign: Optional[models.Campaign] = None) -> str:
    if explicit_instance_name:
        return explicit_instance_name
    if campaign and campaign.evolution_instance_name:
        return campaign.evolution_instance_name
    if campaign:
        return f"user_{campaign.user_id}_whatsapp"
    return f"user_{current_user_id}_whatsapp"


def _apply_whatsapp_status_to_leads(leads: list[models.Lead], validation_results: dict[str, bool]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for lead in leads:
        normalized_phone = whatsapp_service._normalize_phone(lead.phone or "")
        is_whatsapp = validation_results.get(normalized_phone) if normalized_phone else None
        lead.whatsapp_status = _whatsapp_status_for(lead.phone, is_whatsapp)
        items.append({
            "lead_id": lead.id,
            "phone": lead.phone,
            "is_whatsapp": is_whatsapp,
            "whatsapp_status": lead.whatsapp_status,
        })
    return items


@router.post("/upload")
async def upload_leads(
    background_tasks: BackgroundTasks,
    source: str = Form("apollo"),
    sheet_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    validate_whatsapp: bool = Form(False),
    instance_name: Optional[str] = Form(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload leads via CSV or Google Sheet URL.
    Source can be 'apollo' (CSV file) or 'google' (Sheet URL).
    """
    if source == "google":
        if not sheet_url or not sheet_url.strip():
            raise HTTPException(status_code=400, detail="Google Sheet URL is required for Google source")
        try:
            content_str = csv_service.fetch_google_sheet_csv(sheet_url.strip())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif source == "apollo":
        if not file:
            raise HTTPException(status_code=400, detail="CSV file is required for Apollo source")
        if not file.filename or not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed for Apollo source")
        try:
            content = await file.read()
            content_str = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a UTF-8 CSV.")
    else:
        raise HTTPException(status_code=400, detail=f"Invalid source: {source}. Use 'apollo' or 'google'.")

    if validate_whatsapp and not instance_name:
        raise HTTPException(status_code=400, detail="Evolution instance name is required when WhatsApp validation is enabled")

    background_tasks.add_task(process_csv_import, current_user.id, content_str, source, validate_whatsapp, instance_name)
    return {"message": "CSV upload started in background"}


@router.post("/whatsapp/validate-bulk")
async def validate_bulk_whatsapp(
    *,
    db: Session = Depends(deps.get_db),
    payload: schemas.WhatsAppBulkValidateRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Validate a batch of leads against WhatsApp in one Evolution API request.
    """
    if not payload.lead_ids:
        raise HTTPException(status_code=400, detail="No lead ids provided")

    leads = db.query(models.Lead).filter(
        models.Lead.user_id == current_user.id,
        models.Lead.id.in_(payload.lead_ids),
    ).all()

    if not leads:
        raise HTTPException(status_code=404, detail="No leads found")

    instance_name = _resolve_whatsapp_instance_name(current_user.id, payload.instance_name)
    await asyncio.to_thread(whatsapp_service.ensure_instance_sync, instance_name)

    phones = [lead.phone for lead in leads if lead.phone]
    validation_results = await asyncio.to_thread(
        whatsapp_service.check_whatsapp_numbers_sync,
        instance_name,
        phones,
    )

    items = _apply_whatsapp_status_to_leads(leads, validation_results)
    db.add_all(leads)
    db.commit()

    return {
        "instance_name": instance_name,
        "validated": len(items),
        "valid_count": sum(1 for item in items if item["whatsapp_status"] == "valid"),
        "invalid_count": sum(1 for item in items if item["whatsapp_status"] == "invalid"),
        "missing_count": sum(1 for item in items if item["whatsapp_status"] == "missing"),
        "unknown_count": sum(1 for item in items if item["whatsapp_status"] == "unknown"),
        "items": items,
    }

@router.get("/{lead_id}", response_model=schemas.Lead)
def read_lead_by_id(
    lead_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get lead by ID.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.post("/{lead_id}/send")
async def send_lead_email(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    email_send: schemas.EmailSendRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send a single email to a lead using a campaign sequence.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == email_send.campaign_id,
        models.Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    sequence = db.query(models.Sequence).filter(
        models.Sequence.id == email_send.sequence_id,
        models.Sequence.campaign_id == campaign.id,
    ).first()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    result = await email_service.send_cold_email(db, campaign.id, lead.id, sequence.id)
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to send email"))

    return {
        "status": "success",
        "email_id": result.get("email_id"),
        "resend_id": result.get("resend_id"),
    }

@router.get("/{lead_id}/thread")
def read_lead_thread(
    lead_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all sent emails and received replies for a lead, ordered by date.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Fetch sent emails with campaign names
    from app.models.campaign import Campaign
    from app.models.communication import Communication
    email_data = db.query(models.Email, Campaign.name).join(
        Campaign, models.Email.campaign_id == Campaign.id
    ).filter(models.Email.lead_id == lead_id).all()

    comm_data = db.query(Communication, Campaign.name).join(
        Campaign, Communication.campaign_id == Campaign.id
    ).filter(Communication.lead_id == lead_id).all()
    
    # Fetch received replies
    replies = db.query(models.Reply).filter(models.Reply.lead_id == lead_id).all()
 
    # Combine and sort
    thread = []
    campaign_names = set()
    for e, campaign_name in email_data:
        campaign_names.add(campaign_name)
        thread.append({
            "type": "sent",
            "channel": "email",
            "id": e.id,
            "subject": e.subject,
            "content": e.body,
            "timestamp": e.sent_at,
            "campaign_name": campaign_name,
            "status": "opened" if e.opened else ("clicked" if e.clicked else "sent")
        })

    for comm, campaign_name in comm_data:
        campaign_names.add(campaign_name)
        thread.append({
            "type": "sent",
            "channel": comm.channel,
            "id": comm.id,
            "subject": comm.subject,
            "content": comm.body,
            "timestamp": comm.sent_at,
            "campaign_name": campaign_name,
            "status": "replied" if comm.replied else comm.status or "sent"
        })

    for r in replies:
        thread.append({
            "type": "received",
            "id": r.id,
            "subject": f"Re: {lead.company}",
            "content": r.message,
            "timestamp": r.created_at,
            "classification": r.classification
        })
 
    thread.sort(key=lambda x: x["timestamp"])
    
    # Convert lead to dict manually to avoid Pydantic serialization errors with SQLAlchemy objects
    from fastapi.encoders import jsonable_encoder
    return {
        "lead": jsonable_encoder(lead),
        "thread": thread,
        "campaign_name": list(campaign_names)[0] if campaign_names else "No active campaign",
        "total_emails": len(email_data)
    }

@router.put("/{lead_id}", response_model=schemas.Lead)
def update_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    lead_in: schemas.LeadUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a lead.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    update_data = lead_in.dict(exclude_unset=True)
    phone_changed = "phone" in update_data and update_data["phone"] != lead.phone
    for field in update_data:
        setattr(lead, field, update_data[field])

    if phone_changed:
        lead.whatsapp_status = _whatsapp_status_for(lead.phone)
    
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.delete("/{lead_id}", response_model=schemas.Lead)
def delete_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a lead.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    deleted_lead = schemas.Lead.model_validate(lead)

    # Delete dependents first to satisfy the current FK constraints.
    db.query(models.Reply).filter(models.Reply.lead_id == lead_id).delete(synchronize_session=False)
    db.query(models.Email).filter(models.Email.lead_id == lead_id).delete(synchronize_session=False)
    db.query(models.Communication).filter(models.Communication.lead_id == lead_id).delete(synchronize_session=False)
    db.delete(lead)
    db.commit()
    return deleted_lead


@router.post("/{lead_id}/whatsapp")
async def send_lead_whatsapp(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    whatsapp_send: schemas.WhatsAppSendRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send a WhatsApp message to a lead.

    This endpoint supports both direct manual sends and campaign sequence sends.
    If `campaign_id` and `sequence_id` are provided, it sends the corresponding
    WhatsApp campaign sequence message. Otherwise it sends the provided message text.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.phone:
        raise HTTPException(status_code=400, detail="Lead does not have a phone number")

    if whatsapp_send.campaign_id is not None or whatsapp_send.sequence_id is not None:
        if whatsapp_send.campaign_id is None or whatsapp_send.sequence_id is None:
            raise HTTPException(status_code=400, detail="Both campaign_id and sequence_id are required for campaign sends")

        campaign = db.query(models.Campaign).filter(
            models.Campaign.id == whatsapp_send.campaign_id,
            models.Campaign.user_id == current_user.id,
        ).first()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.channel != "whatsapp":
            raise HTTPException(status_code=400, detail="Campaign is not configured for WhatsApp")

        sequence = db.query(models.Sequence).filter(
            models.Sequence.id == whatsapp_send.sequence_id,
            models.Sequence.campaign_id == campaign.id,
        ).first()
        if not sequence:
            raise HTTPException(status_code=404, detail="Sequence not found")

        body = _render_whatsapp_body(sequence.body, lead)
        if not body.strip():
            raise HTTPException(status_code=400, detail="WhatsApp sequence body is empty")

        instance_name = _resolve_whatsapp_instance_name(current_user.id, whatsapp_send.instance_name, campaign)
        await asyncio.to_thread(whatsapp_service.ensure_instance_sync, instance_name)
        phone_valid = await asyncio.to_thread(whatsapp_service.is_whatsapp_number_sync, instance_name, lead.phone)
        lead.whatsapp_status = _whatsapp_status_for(lead.phone, phone_valid)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        if phone_valid is False:
            raise HTTPException(status_code=400, detail="Lead phone number is not registered on WhatsApp")
        if phone_valid is None:
            raise HTTPException(status_code=502, detail="Could not validate lead phone number on WhatsApp")
        if sequence.mediatype and sequence.media:
            success = await asyncio.to_thread(
                whatsapp_service.send_media_sync,
                instance_name,
                lead.phone,
                sequence.media,
                sequence.mediatype,
                sequence.mimetype or "application/octet-stream",
                sequence.caption or body
            )
        else:
            success = await asyncio.to_thread(whatsapp_service.send_message_sync, instance_name, lead.phone, body)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send WhatsApp campaign message")

        comm = Communication(
            campaign_id=campaign.id,
            lead_id=lead.id,
            sequence_id=sequence.id,
            channel="whatsapp",
            provider="evolution",
            provider_id=None,
            subject=sequence.subject + (" (Media)" if sequence.media else ""),
            body=body or sequence.caption or "[Media Attachment]",
            status="sent",
            sent_at=datetime.now(timezone.utc)
        )
        db.add(comm)
        db.commit()
        db.refresh(comm)

        return {
            "status": "success",
            "message": "WhatsApp campaign message sent successfully",
            "communication_id": comm.id,
        }

    if not whatsapp_send.message and not whatsapp_send.media:
        raise HTTPException(status_code=400, detail="Message text or media is required for manual WhatsApp send")

    instance_name = _resolve_whatsapp_instance_name(current_user.id, whatsapp_send.instance_name)
    await asyncio.to_thread(whatsapp_service.ensure_instance_sync, instance_name)
    phone_valid = await asyncio.to_thread(whatsapp_service.is_whatsapp_number_sync, instance_name, lead.phone)
    lead.whatsapp_status = _whatsapp_status_for(lead.phone, phone_valid)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    if phone_valid is False:
        raise HTTPException(status_code=400, detail="Lead phone number is not registered on WhatsApp")
    if phone_valid is None:
        raise HTTPException(status_code=502, detail="Could not validate lead phone number on WhatsApp")
    if whatsapp_send.mediatype and whatsapp_send.media:
        if not whatsapp_send.mimetype:
            raise HTTPException(status_code=400, detail="mimetype is required when sending media")
        success = await asyncio.to_thread(
            whatsapp_service.send_media_sync,
            instance_name,
            lead.phone,
            whatsapp_send.media,
            whatsapp_send.mediatype,
            whatsapp_send.mimetype,
            whatsapp_send.caption or whatsapp_send.message,
        )
    else:
        success = await asyncio.to_thread(whatsapp_service.send_message_sync, instance_name, lead.phone, whatsapp_send.message)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send WhatsApp message")

    comm = Communication(
        campaign_id=None,
        lead_id=lead.id,
        sequence_id=None,
        channel="whatsapp",
        provider="evolution",
        provider_id=None,
        subject="Manual WhatsApp Message" + (" (Media)" if whatsapp_send.media else ""),
        body=whatsapp_send.message or whatsapp_send.caption or "[Media Attachment]",
        status="sent",
        sent_at=datetime.now(timezone.utc)
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)

    return {
        "status": "success",
        "message": "WhatsApp message sent successfully",
        "communication_id": comm.id,
    }


@router.post("/{lead_id}/whatsapp/validate")
async def validate_lead_whatsapp(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    instance_name: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Validate whether a lead's phone number is registered on WhatsApp.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.phone:
        raise HTTPException(status_code=400, detail="Lead does not have a phone number")

    resolved_instance_name = _resolve_whatsapp_instance_name(current_user.id, instance_name)
    await asyncio.to_thread(whatsapp_service.ensure_instance_sync, resolved_instance_name)
    is_whatsapp = await asyncio.to_thread(whatsapp_service.is_whatsapp_number_sync, resolved_instance_name, lead.phone)

    if is_whatsapp is None:
        lead.whatsapp_status = _whatsapp_status_for(lead.phone, is_whatsapp)
        db.add(lead)
        db.commit()
        raise HTTPException(status_code=502, detail="Could not validate lead phone number on WhatsApp")

    lead.whatsapp_status = _whatsapp_status_for(lead.phone, is_whatsapp)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return {
        "lead_id": lead.id,
        "phone": lead.phone,
        "instance_name": resolved_instance_name,
        "is_whatsapp": is_whatsapp,
        "whatsapp_status": lead.whatsapp_status,
    }
