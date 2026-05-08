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
    # In production, verify the signature here
    
    payload = await request.json()
    event_type = payload.get("type")
    data = payload.get("data", {})
    email_id = data.get("email_id") # Resend's internal ID
    
    if event_type in ["email.opened", "email.clicked"]:
        email_service.track_webhook_event(db, event_type, email_id)
        
    elif event_type == "email.bounced":
        # Handle bounce: mark lead as invalid or stop campaign
        pass
        
    return {"status": "ok"}

@router.post("/reply")
async def handle_incoming_reply(
    request: Request,
    db: Session = Depends(deps.get_db)
):
    """
    Handle incoming email replies (usually forwarded from an inbox or via email provider API).
    """
    payload = await request.json()
    lead_email = payload.get("from")
    message_body = payload.get("body")
    
    # 1. Find the lead
    lead = db.query(Lead).filter(Lead.email == lead_email).first()
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
    
    # 4. Update lead status and stop sequences if needed
    lead.status = "replied"
    # Logic to stop future emails for this lead in all active campaigns
    
    db.commit()
    
    return {"status": "success", "classification": classification}