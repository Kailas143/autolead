from app.celery_app import celery_app
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services import email_service
import resend
from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY

@celery_app.task
def send_email_task(email_id: int):
    """
    Send an email using Resend API.
    """
    db: Session = SessionLocal()
    try:
        # Use the unified send_email method which includes Zoho SMTP fallback
        import asyncio
        result = asyncio.run(email_service.send_email(db, email_id))
        return result
    finally:
        db.close()

@celery_app.task
def send_followup_task(campaign_id: int, lead_id: int, sequence_step: int):
    """
    Send a follow-up email in a sequence.
    """
    db: Session = SessionLocal()
    try:
        # Get the next sequence email
        sequence_email = email_service.get_next_sequence_email(
            db, campaign_id=campaign_id, lead_id=lead_id, step=sequence_step
        )
        if sequence_email:
            send_email_task.delay(sequence_email.id)
    finally:
        db.close()