# pyrefly: ignore [missing-import]
import resend
import postmark
import requests
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
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

    def _should_fallback(self, error: Exception) -> bool:
        if not settings.POSTMARK_API_KEY and not settings.MAILTRAP_API_TOKEN and not settings.ZOHO_SMTP_USER:
            return False
        message = str(error).lower()
        # Handle Resend specific error messages and common rate limit/quota keywords
        return any(keyword in message for keyword in [
            "quota", 
            "limit", 
            "exceeded", 
            "429", 
            "rate_limit", 
            "monthly sending limit",
            "daily sending limit"
        ])

    async def _send_via_postmark_sdk(self, from_email: str, to_email: str, subject: str, html_body: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends email using the official postmark-python SDK.
        """
        client = postmark.ServerClient(settings.POSTMARK_API_KEY)
        payload = {
            "From": from_email,
            "To": to_email,
            "Subject": subject,
            "HtmlBody": html_body,
        }
        if reply_to:
            payload["ReplyTo"] = reply_to
            
        # Run synchronous SDK call in a thread
        response = await asyncio.to_thread(client.emails.send, **payload)
        return {"MessageID": response.get('MessageID'), "ErrorCode": response.get('ErrorCode'), "Message": response.get('Message')}

    def _send_smtp_sync(self, to_email: str, subject: str, html_body: str, from_email: Optional[str] = None):
        """
        Synchronous SMTP sending logic to be run in a thread.
        """
        if not settings.ZOHO_SMTP_USER or not settings.ZOHO_SMTP_PASSWORD:
            raise ValueError("Zoho SMTP credentials not configured")

        msg = MIMEMultipart()
        msg["From"] = from_email or f"{settings.EMAIL_FROM_NAME} <{settings.ZOHO_SMTP_USER}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html"))

        # Zoho usually uses port 465 for SSL or 587 for TLS
        if settings.ZOHO_SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.ZOHO_SMTP_HOST, settings.ZOHO_SMTP_PORT) as server:
                server.login(settings.ZOHO_SMTP_USER, settings.ZOHO_SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.ZOHO_SMTP_HOST, settings.ZOHO_SMTP_PORT) as server:
                server.starttls()
                server.login(settings.ZOHO_SMTP_USER, settings.ZOHO_SMTP_PASSWORD)
                server.send_message(msg)

    async def _send_via_zoho_smtp(self, to_email: str, subject: str, html_body: str, from_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends email using Zoho SMTP (running blocking SMTP in a thread).
        """
        await asyncio.to_thread(self._send_smtp_sync, to_email, subject, html_body, from_email)
        return {"MessageID": f"zoho-{datetime.now().timestamp()}", "Status": "Success"}

    async def _send_via_mailtrap_api(self, to_email: str, subject: str, html_body: str) -> Dict[str, Any]:
        """
        Sends email using Mailtrap API.
        """
        if not settings.MAILTRAP_API_TOKEN:
            raise ValueError("Mailtrap API token not configured")

        url = "https://send.api.mailtrap.io/api/send"
        headers = {
            "Authorization": f"Bearer {settings.MAILTRAP_API_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": {"email": settings.EMAIL_FROM, "name": settings.EMAIL_FROM_NAME},
            "to": [{"email": to_email}],
            "subject": subject,
            "html": html_body,
        }

        # Run blocking requests in a thread
        response = await asyncio.to_thread(requests.post, url, json=payload, headers=headers)
        
        if response.status_code not in [200, 202]:
            raise Exception(f"Mailtrap API failed: {response.text}")
            
        data = response.json()
        return {"MessageID": data.get("message_ids", [""])[0], "Status": "Success"}

    async def send_cold_email(self, db: Session, campaign_id: int, lead_id: int, sequence_id: int) -> Dict[str, Any]:
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
            # Check if we should use test mode (for development)
            if settings.EMAIL_SERVICE_MODE == "test":
                print(f"DEBUG [TEST MODE]: Would send email to {lead.email}")
                r = {"id": f"test-{campaign_id}-{lead_id}"}
            else:
                r = resend.Emails.send(params)
            
            # Record the email in the database
            email_record = Email(
                lead_id=lead.id,
                campaign_id=campaign_id,
                sequence_id=sequence_id,
                subject=subject,
                body=plain_body,
                resend_id=r["id"],
                sent_at=datetime.now(timezone.utc)
            )
            db.add(email_record)
            db.commit()
            db.refresh(email_record)
            
            print(f"DEBUG: Successfully saved email to database. ID: {email_record.id}, Resend ID: {r['id']}")
            return {"status": "success", "email_id": email_record.id, "resend_id": r["id"]}
        except Exception as e:
            error_text = str(e)
            print(f"ERROR: Resend email send failed: {error_text}")
            if self._should_fallback(e):
                provider = None
                msg_id = None
                fallback_response = None
                
                # 1. Attempt Postmark Fallback (First Priority)
                if settings.POSTMARK_API_KEY:
                    try:
                        print("DEBUG: Falling back to Postmark due to Resend quota issue")
                        fallback_response = await self._send_via_postmark_sdk(
                            f"{settings.POSTMARK_SENDER}",
                            lead.email,
                            subject,
                            html_body,
                            reply_to=params.get("reply_to")
                        )
                        provider = "postmark"
                        msg_id = fallback_response.get('MessageID', '')
                    except Exception as pe:
                        print(f"ERROR: Postmark fallback failed: {pe}")

                # 2. Attempt Mailtrap Fallback (Second Priority)
                if not provider and settings.MAILTRAP_API_TOKEN:
                    try:
                        print("DEBUG: Falling back to Mailtrap")
                        fallback_response = await self._send_via_mailtrap_api(
                            lead.email,
                            subject,
                            html_body
                        )
                        provider = "mailtrap"
                        msg_id = fallback_response.get('MessageID', '')
                    except Exception as mt:
                        print(f"ERROR: Mailtrap fallback failed: {mt}")

                # 3. Attempt Zoho SMTP Fallback if previous providers failed or not configured
                if not provider and settings.ZOHO_SMTP_USER:
                    try:
                        print("DEBUG: Falling back to Zoho SMTP")
                        fallback_response = await self._send_via_zoho_smtp(
                            lead.email,
                            subject,
                            html_body
                        )
                        provider = "zoho"
                        msg_id = fallback_response.get('MessageID', '')
                    except Exception as ze:
                        print(f"ERROR: Zoho fallback failed: {ze}")

                if provider:
                    try:
                        email_record = Email(
                            lead_id=lead.id,
                            campaign_id=campaign_id,
                            sequence_id=sequence_id,
                            subject=subject,
                            body=plain_body,
                            resend_id=f"{provider}-{msg_id}",
                            sent_at=datetime.now(timezone.utc)
                        )
                        db.add(email_record)
                        db.commit()
                        db.refresh(email_record)
                        print(f"DEBUG: {provider.capitalize()} fallback succeeded. Email ID: {email_record.id}")
                        return {
                            "status": "success",
                            "email_id": email_record.id,
                            "resend_id": email_record.resend_id,
                            "provider": provider,
                            "provider_response": fallback_response,
                        }
                    except Exception as db_error:
                        print(f"ERROR: Failed to save fallback email to DB: {db_error}")
                        return {"status": "error", "message": f"Fallback succeeded but DB save failed: {db_error}"}
                else:
                    return {"status": "error", "message": f"{error_text} | All fallbacks failed or were unconfigured."}

            return {"status": "error", "message": error_text}

    def get_by_id(self, db: Session, id: int) -> Optional[Email]:
        return db.query(Email).filter(Email.id == id).first()

    def update_sent_status(self, db: Session, email_id: int, sent_at: bool = True):
        email = self.get_by_id(db, email_id)
        if email:
            if sent_at:
                email.sent_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(email)
        return email

    async def send_email(self, db: Session, email_id: int) -> Dict[str, Any]:
        """
        Generic method to send an existing email record.
        Includes Postmark fallback.
        """
        email_record = self.get_by_id(db, email_id)
        if not email_record:
            return {"status": "error", "message": "Email record not found"}

        params = {
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
            "to": [email_record.lead.email],
            "subject": email_record.subject,
            "html": email_record.body, # Assuming body is HTML or we wrap it
        }

        try:
            if settings.EMAIL_SERVICE_MODE == "test":
                print(f"DEBUG [TEST MODE]: Would send email {email_id}")
                resend_id = f"test-{email_id}"
            else:
                r = resend.Emails.send(params)
                resend_id = r["id"]
            
            email_record.resend_id = resend_id
            email_record.sent_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "success", "resend_id": resend_id}
        except Exception as e:
            if self._should_fallback(e):
                provider = None
                msg_id = None
                
                # 1. Attempt Postmark Fallback (First Priority)
                if settings.POSTMARK_API_KEY:
                    try:
                        fallback = await self._send_via_postmark_sdk(
                            settings.POSTMARK_SENDER,
                            email_record.lead.email,
                            email_record.subject,
                            email_record.body,
                        )
                        provider = "postmark"
                        msg_id = fallback.get('MessageID', '')
                    except Exception as pe:
                        print(f"ERROR: Postmark fallback failed: {pe}")

                # 2. Attempt Mailtrap Fallback (Second Priority)
                if not provider and settings.MAILTRAP_API_TOKEN:
                    try:
                        fallback = await self._send_via_mailtrap_api(
                            email_record.lead.email,
                            email_record.subject,
                            email_record.body,
                        )
                        provider = "mailtrap"
                        msg_id = fallback.get('MessageID', '')
                    except Exception as mt:
                        print(f"ERROR: Mailtrap fallback failed: {mt}")

                # 3. Attempt Zoho SMTP Fallback if previous providers failed or not configured
                if not provider and settings.ZOHO_SMTP_USER:
                    try:
                        fallback = await self._send_via_zoho_smtp(
                            email_record.lead.email,
                            email_record.subject,
                            email_record.body,
                        )
                        provider = "zoho"
                        msg_id = fallback.get('MessageID', '')
                    except Exception as ze:
                        print(f"ERROR: Zoho fallback failed: {ze}")

                if provider:
                    email_record.resend_id = f"{provider}-{msg_id}"
                    email_record.sent_at = datetime.now(timezone.utc)
                    db.commit()
                    return {"status": "success", "resend_id": email_record.resend_id, "provider": provider}
                else:
                    return {"status": "error", "message": f"Resend failed: {e} | All fallbacks failed."}
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
