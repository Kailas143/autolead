
from app.core.database import SessionLocal
from app.services.whatsapp_service import whatsapp_service
from app.models.lead import Lead
from app.models.campaign import Campaign, Sequence
from app.models.communication import Communication
from app.utils.template_vars import replace_template_vars
from datetime import datetime, timezone


def _campaign_instance_name(campaign: Campaign) -> str:
    return campaign.evolution_instance_name or f"user_{campaign.user_id}_whatsapp"


def _whatsapp_status_for(phone: str | None, is_whatsapp: bool | None = None) -> str:
    if not phone or not phone.strip():
        return "missing"
    if is_whatsapp is True:
        return "valid"
    if is_whatsapp is False:
        return "invalid"
    return "unknown"


def send_whatsapp_message_task(campaign_id: int, lead_id: int, sequence_id: int):
    """Send a WhatsApp message via Evolution API."""
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()

        if not (campaign and lead and sequence):
            return False

        if not lead.phone:
            print(f"DEBUG: Skipping WhatsApp message for lead {lead.id} - No phone number")
            return False

        body = replace_template_vars(sequence.body, {
            "first_name": lead.first_name or "",
            "last_name": lead.last_name or "",
            "company": lead.company or "",
            "title": lead.title or "",
            "industry": lead.industry or "",
        })

        instance_name = _campaign_instance_name(campaign)
        whatsapp_service.ensure_instance_sync(instance_name)
        is_whatsapp = whatsapp_service.is_whatsapp_number_sync(instance_name, lead.phone)
        lead.whatsapp_status = _whatsapp_status_for(lead.phone, is_whatsapp)
        db.add(lead)
        db.commit()
        if is_whatsapp is False:
            print(f"DEBUG: [whatsapp] Skipping lead {lead.id} - phone {lead.phone} is not on WhatsApp")
            return False
        if is_whatsapp is None:
            print(f"DEBUG: [whatsapp] Skipping lead {lead.id} - could not validate phone {lead.phone}")
            return False

        if sequence.mediatype and sequence.media:
            # We can use the sequence caption or fallback to the body if caption is missing
            success = whatsapp_service.send_media_sync(
                instance_name,
                lead.phone,
                sequence.media,
                sequence.mediatype,
                sequence.mimetype or "application/octet-stream",
                sequence.caption or body
            )
        else:
            success = whatsapp_service.send_message_sync(instance_name, lead.phone, body)

        if success and sequence.poll_question and sequence.poll_options:
            whatsapp_service.send_poll_sync(
                instance_name, 
                lead.phone, 
                sequence.poll_question, 
                sequence.poll_options
            )

        if success:
            log = Communication(
                campaign_id=campaign.id,
                lead_id=lead.id,
                sequence_id=sequence.id,
                channel="whatsapp",
                provider="evolution",
                provider_id=None,
                subject="WhatsApp Message" + (" (Media)" if sequence.media else ""),
                body=body or sequence.caption or "[Media Attachment]",
                status="sent",
                sent_at=datetime.now(timezone.utc)
            )
            db.add(log)
            db.commit()
            print(f"DEBUG: [whatsapp] Campaign {campaign.id} sent message to {lead.phone}")
            return True
        return False
    except Exception as e:
        from app.services.audit_service import audit_service
        audit_service.log_error(db, "WHATSAPP", f"Failed to send whatsapp message to lead {lead_id}", e)
        return False
    finally:
        db.close()

def process_whatsapp_campaigns():
    """Periodic task to process and queue WhatsApp campaign messages."""
    from app.workers.tasks import check_whatsapp_follow_ups
    check_whatsapp_follow_ups()
