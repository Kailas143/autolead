import resend
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.email import Email
from app.models.lead import Lead
from app.models.campaign import Campaign, Sequence
from app.schemas.email import EmailCreate

class EmailService:
    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY

    def send_cold_email(self, db: Session, campaign_id: int, lead_id: int, sequence_id: int) -> Dict[str, Any]:
        """
        Sends a cold email to a lead as part of a campaign sequence.
        """
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()
        
        if not lead or not sequence:
            return {"status": "error", "message": "Lead or Sequence not found"}

        # Prepare email content
        # In a real app, you'd replace placeholders in sequence.body with lead data
        # and AI-generated personalization lines.
        body = sequence.body.format(
            first_name=lead.first_name,
            company=lead.company,
            personalization=lead.industry # Placeholder for AI line
        )

        params = {
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
            "to": [lead.email],
            "subject": sequence.subject,
            "html": body,
        }

        try:
            r = resend.Emails.send(params)
            
            # Record the email in the database
            email_record = Email(
                lead_id=lead.id,
                campaign_id=campaign_id,
                sequence_id=sequence_id,
                subject=sequence.subject,
                body=body,
                sent_at=datetime.utcnow()
            )
            db.add(email_record)
            db.commit()
            db.refresh(email_record)
            
            return {"status": "success", "email_id": email_record.id, "resend_id": r["id"]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def track_webhook_event(self, db: Session, event_type: str, email_id: str):
        """
        Updates email status based on Resend webhooks.
        """
        # Logic to map Resend's internal ID to our database ID
        # For simplicity, we assume we have a way to find the email
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            return

        if event_type == "email.opened":
            email.opened = True
        elif event_type == "email.clicked":
            email.clicked = True
        
        db.commit()

email_service = EmailService()