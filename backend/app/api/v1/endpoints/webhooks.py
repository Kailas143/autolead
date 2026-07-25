import json
import re
from html import unescape
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.models.lead import Lead
from app.models.reply import Reply
from app.services.ai_service import ai_service
from app.services.email_service import email_service

router = APIRouter()


def _strip_html(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<br\s*/?>", "\n", text)
    text = re.sub(r"(?s)</p\s*>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_candidate_text(payload: Any, candidate_keys: tuple[str, ...]) -> str:
    if isinstance(payload, dict):
        for key in candidate_keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for value in payload.values():
            extracted = _extract_candidate_text(value, candidate_keys)
            if extracted:
                return extracted

    if isinstance(payload, list):
        for item in payload:
            extracted = _extract_candidate_text(item, candidate_keys)
            if extracted:
                return extracted

    return ""


def _extract_message_body(payload: dict[str, Any]) -> str:
    data = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}

    text_candidates = (
        "text",
        "body",
        "plain",
        "plainText",
        "plain_text",
        "textBody",
        "text_body",
        "stripped-text",
        "strippedText",
        "snippet",
        "reply",
    )
    html_candidates = (
        "html",
        "htmlBody",
        "html_body",
        "stripped-html",
        "strippedHtml",
    )

    text_value = _extract_candidate_text(data or payload, text_candidates)
    if text_value:
        return text_value

    html_value = _extract_candidate_text(data or payload, html_candidates)
    if html_value:
        return _strip_html(html_value)

    return ""

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
            # Mirror to Communication if present
            try:
                from app.models.communication import Communication
                comm = db.query(Communication).filter(Communication.provider_id == email.resend_id).first()
                if comm:
                    comm.replied = True
                    db.add(comm)
            except Exception:
                db.rollback()
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
    print(f"DEBUG: Webhook payload: {json.dumps(payload)}")
    
    # Check if this is a Resend 'email.received' event structure
    if payload.get("type") == "email.received":
        data = payload.get("data", {})
        from_header = data.get("from", "")
        message_body = _extract_message_body(payload)
        
        print(f"DEBUG: Received Resend email event from {from_header}. Body length: {len(message_body) if message_body else 0}")
    else:
        # Fallback for simple direct POSTs
        from_header = payload.get("from", "")
        message_body = _extract_message_body(payload)
        print(f"DEBUG: Received direct POST from {from_header}. Body length: {len(message_body) if message_body else 0}")
    
    # 1. Parse email address from 'From' header (e.g. "Name <email@addr.com>")
    from email.utils import parseaddr
    _, lead_email = parseaddr(from_header)
    
    if not lead_email:
        # Fallback if parseaddr fails or header is just the email
        lead_email = from_header.strip()

    if not lead_email:
        print(f"ERROR: Missing sender email in payload: {json.dumps(payload)}")
        raise HTTPException(status_code=400, detail="Missing sender email")

    # 2. Find the lead (case-insensitive)
    lead = db.query(Lead).filter(Lead.email.ilike(lead_email)).first()
    if not lead:
        print(f"DEBUG: Lead not found for email: {lead_email}")
        return {"status": "lead not found"}
        
    # 3. Find the most recent email sent to this lead to link the reply
    from app.models.email import Email
    last_email = db.query(Email).filter(
        Email.lead_id == lead.id
    ).order_by(Email.sent_at.desc()).first()

    # 4. Robust message body extraction
    subject = payload.get("data", {}).get("subject", "No Subject")
    final_message = message_body.strip() if message_body else ""
        
    if not final_message:
        final_message = f"[No body content - Subject: {subject}]"

    # 5. Classify the reply using AI (with fallback)
    classification = "other"
    try:
        # Pass the message or subject to the classifier
        text_to_classify = message_body.strip() if (message_body and message_body.strip()) else subject
        classification = await ai_service.classify_reply(text_to_classify, db=db, user_id=lead.user_id)
    except Exception as e:
        print(f"ERROR: AI classification failed: {str(e)}")
    
    # 6. Store the reply
    new_reply = Reply(
        lead_id=lead.id,
        email_id=last_email.id if last_email else None,
        message=final_message,
        classification=classification
    )
    db.add(new_reply)
    
    # 6. Update lead status
    lead.status = "replied"
    
    # 7. Mark the email record as replied
    if last_email:
        last_email.replied = True
        # Mirror to Communication if present
        try:
            from app.models.communication import Communication
            comm = db.query(Communication).filter(Communication.provider_id == last_email.resend_id).first()
            if comm:
                comm.replied = True
                db.add(comm)
        except Exception:
            db.rollback()
    
    db.commit()
    
    return {"status": "success", "classification": classification, "reply_id": new_reply.id}
