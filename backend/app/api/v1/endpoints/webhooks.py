from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.services.email_service import email_service
from app.services.ai_service import ai_service
from app.models.lead import Lead
from app.models.reply import Reply
import json

router = APIRouter()

@router.post("/resend")
async def resend_webhook(
    request: Request,
    db: Session = Depends(deps.get_db),
    x_resend_signature: str = Header(None)
):
    """
    Endpoint for Resend webhooks to track email events.
    """
    payload = await request.json()
    event_type = payload.get("type")
    data = payload.get("data", {})
    resend_email_id = data.get("email_id")
    
    if event_type in ["email.opened", "email.clicked"]:
        email_service.track_webhook_event(db, event_type, resend_email_id)
        
    elif event_type == "email.replied":
        # Handle reply from Resend's tracking
        from app.models.email import Email
        email = db.query(Email).filter(Email.resend_id == resend_email_id).first()
        if email:
            email.replied = True
            lead = db.query(Lead).filter(Lead.id == email.lead_id).first()
            if lead:
                lead.status = "replied"
            db.commit()
            
    return {"status": "ok"}

@router.post("/reply")
async def handle_incoming_reply(
    request: Request,
    db: Session = Depends(deps.get_db)
):
    """
    Handle incoming email replies (usually forwarded from an inbox).
    """
    payload = await request.json()
    
    # Check if this is a Resend 'email.received' event structure
    if payload.get("type") == "email.received":
        data = payload.get("data", {})
        from_header = data.get("from", "")
        message_body = data.get("text", "") or data.get("html", "")
    else:
        # Fallback for simple direct POSTs
        from_header = payload.get("from", "")
        message_body = payload.get("body", "")
    
    # 1. Parse email address from 'From' header (e.g. "Name <email@addr.com>")
    from email.utils import parseaddr
    _, lead_email = parseaddr(from_header)
    
    if not lead_email:
        # Fallback if parseaddr fails or header is just the email
        lead_email = from_header.strip()

    if not lead_email:
        raise HTTPException(status_code=400, detail="Missing sender email")

    # 2. Find the lead (case-insensitive)
    lead = db.query(Lead).filter(Lead.email.ilike(lead_email)).first()
    if not lead:
        print(f"DEBUG: Lead not found for email: {lead_email}")
        return {"status": "lead not found"}
        
    # 3. Classify the reply using AI (with fallback)
    classification = "other"
    try:
        classification = await ai_service.classify_reply(message_body)
    except Exception as e:
        print(f"ERROR: AI classification failed: {str(e)}")
        # Continue with 'other' classification so we don't lose the reply
    
    # 4. Store the reply
    new_reply = Reply(
        lead_id=lead.id,
        message=message_body,
        classification=classification
    )
    db.add(new_reply)
    
    # 5. Update lead status
    lead.status = "replied"
    
    # 6. Mark the most recent email sent to this lead as 'replied'
    from app.models.email import Email
    last_email = db.query(Email).filter(
        Email.lead_id == lead.id
    ).order_by(Email.sent_at.desc()).first()
    
    if last_email:
        last_email.replied = True
    
    db.commit()
    
    return {"status": "success", "classification": classification, "lead_id": lead.id}