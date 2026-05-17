from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app import schemas, models
from app.api import deps
from app.services.csv_service import csv_service
from app.services.email_service import email_service
from app.workers.tasks import process_csv_import

router = APIRouter()

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
    lead = models.Lead(
        **lead_in.dict(),
        user_id=current_user.id,
        status="new"
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.post("/upload")
async def upload_leads(
    source: str = Form("apollo"),
    sheet_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
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

    process_csv_import.delay(current_user.id, content_str, source)
    return {"message": "CSV upload started in background"}

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
    email_data = db.query(models.Email, Campaign.name).join(
        Campaign, models.Email.campaign_id == Campaign.id
    ).filter(models.Email.lead_id == lead_id).all()
    
    # Fetch received replies
    replies = db.query(models.Reply).filter(models.Reply.lead_id == lead_id).all()
 
    # Combine and sort
    thread = []
    campaign_names = set()
    for e, campaign_name in email_data:
        campaign_names.add(campaign_name)
        thread.append({
            "type": "sent",
            "id": e.id,
            "subject": e.subject,
            "content": e.body,
            "timestamp": e.sent_at,
            "campaign_name": campaign_name,
            "status": "opened" if e.opened else ("sent" if not e.opened else "clicked")
        })
    
    for r in replies:
        thread.append({
            "type": "received",
            "id": r.id,
            "subject": f"Re: {lead.company}", # Fallback
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
    for field in update_data:
        setattr(lead, field, update_data[field])
    
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
    db.delete(lead)
    db.commit()
    return deleted_lead
