# pyrefly: ignore [missing-import]
import resend
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.email import Email
from app.models.lead import Lead
from app.models.campaign import Campaign, Sequence
from app.schemas.email import EmailCreate

import re

class EmailService:
    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY

    def _replace_vars(self, text: str, vars: Dict[str, str]) -> str:
        """
        Robustly replaces variables in text, handling {var}, {{var}}, and { var }.
        """
        if not text:
            return ""
        for key, value in vars.items():
            # Handle {key}, {{key}}, { key }, {{ key }}
            pattern = r"\{{1,2}\s*" + re.escape(key) + r"\s*\}{1,2}"
            text = re.sub(pattern, str(value), text)
        return text

    def send_cold_email(self, db: Session, campaign_id: int, lead_id: int, sequence_id: int) -> Dict[str, Any]:
        """
        Sends a cold email to a lead as part of a campaign sequence.
        """
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()
        
        if not lead or not sequence:
            return {"status": "error", "message": "Lead or Sequence not found"}

        # Prepare content variables
        content_vars = {
            "first_name": lead.first_name or "there",
            "company": lead.company or "your company",
            "industry": lead.industry or "your space",
            "personalization": lead.industry or "" # Default to industry if AI not run
        }

        # Robust replacement for both subject and body
        subject = self._replace_vars(sequence.subject, content_vars)
        plain_body = self._replace_vars(sequence.body, content_vars)

        # Create Professional HTML Template
        # Convert double newlines to paragraphs and single newlines to line breaks
        html_content = plain_body.replace("\n\n", "</div><div style='margin-bottom: 16px;'>").replace("\n", "<br>")
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Inter', sans-serif; -webkit-font-smoothing: antialiased; margin: 0; padding: 0; }}
            </style>
        </head>
        <body style="background-color: #f9fafb; padding: 40px 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; border: 1px solid #e5e7eb; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <div style="padding: 40px;">
                    <div style="font-size: 16px; line-height: 1.7; color: #374151;">
                        <div style="margin-bottom: 16px;">{html_content}</div>
                    </div>
                    
                    <div style="margin-top: 40px; padding-top: 32px; border-top: 1px solid #f3f4f6;">
                        <table border="0" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="padding-right: 16px;">
                                    <div style="width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, #000 0%, #333 100%); color: #fff; text-align: center; line-height: 48px; font-weight: 600; font-size: 20px;">
                                        {settings.EMAIL_FROM_NAME[0] if settings.EMAIL_FROM_NAME else 'A'}
                                    </div>
                                </td>
                                <td>
                                    <div style="font-size: 15px; font-weight: 600; color: #111827;">{settings.EMAIL_FROM_NAME}</div>
                                    <div style="font-size: 13px; color: #6b7280; margin-bottom: 4px;">Aurvyz | Intelligence, Engineered</div>
                                    <div style="font-size: 13px;">
                                        <span style="margin-right: 4px;">📩</span> <a href="mailto:{settings.EMAIL_FROM}" style="color: #2563eb; text-decoration: none; font-weight: 500;">{settings.EMAIL_FROM}</a>
                                        <span style="color: #d1d5db; margin: 0 12px;">•</span>
                                        <span style="margin-right: 4px;">🌐</span> <a href="https://www.aurvyz.com" style="color: #2563eb; text-decoration: none; font-weight: 500;">www.aurvyz.com</a>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 24px; font-size: 12px; color: #9ca3af;">
                Intelligence for Consultancies • Built by Aurvyz
            </div>
        </body>
        </html>
        """

        params = {
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
            "to": [lead.email],
            "reply_to": "reply@ulduudiitu.resend.app",
            "subject": subject,
            "html": html_body,
        }

        try:
            r = resend.Emails.send(params)
            
            # Record the email in the database
            email_record = Email(
                lead_id=lead.id,
                campaign_id=campaign_id,
                sequence_id=sequence_id,
                subject=subject,
                body=plain_body,
                resend_id=r["id"],
                sent_at=datetime.utcnow()
            )
            db.add(email_record)
            db.commit()
            db.refresh(email_record)
            
            print(f"DEBUG: Successfully saved email to database. ID: {email_record.id}, Resend ID: {r['id']}")
            return {"status": "success", "email_id": email_record.id, "resend_id": r["id"]}
        except Exception as e:
            print(f"ERROR: Failed to save email to database: {str(e)}")
            return {"status": "error", "message": str(e)}

    def track_webhook_event(self, db: Session, event_type: str, email_id: str):
        """
        Updates email status based on Resend webhooks.
        """
        # Logic to map Resend's internal ID to our database ID
        email = db.query(Email).filter(Email.resend_id == email_id).first()
        if not email:
            return

        if event_type == "email.opened":
            email.opened = True
        elif event_type == "email.clicked":
            email.clicked = True
        
        db.commit()

email_service = EmailService()