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
    lead_email = payload.get("from")
    message_body = payload.get("body")
    
    if not lead_email:
        raise HTTPException(status_code=400, detail="Missing sender email")

    # 1. Find the lead (case-insensitive)
    lead = db.query(Lead).filter(Lead.email.ilike(lead_email)).first()
    if not lead:
        return {"status": "lead not found"}
        
    # 2. Classify the reply using AI
    classification = await ai_service.classify_reply(message_body)
    
    # 3. Store the reply
    new_reply = Reply(
        lead_id=lead.id,
        message=message_body,
        classification=classification
    )
    db.add(new_reply)
    
    # 4. Update lead status
    lead.status = "replied"
    
    # 5. Mark the most recent email sent to this lead as 'replied'
    from app.models.email import Email
    last_email = db.query(Email).filter(
        Email.lead_id == lead.id
    ).order_by(Email.sent_at.desc()).first()
    
    if last_email:
        last_email.replied = True
    
    db.commit()
    
    return {"status": "success", "classification": classification, "lead_id": lead.id}