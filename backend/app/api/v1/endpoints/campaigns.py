from datetime import datetime, timezone
from typing import Any, List, Dict
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app import schemas, models
from app.api import deps
from app.services.whatsapp_service import whatsapp_service
from app.models.communication import Communication
from app.utils.template_vars import replace_template_vars
from app.workers.tasks import launch_campaign_task, check_follow_ups
from app.core.config import settings
from fastapi import Header, BackgroundTasks

router = APIRouter()


def _to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _render_whatsapp_body(template: str, lead: models.Lead) -> str:
    replacements = {
        "first_name": lead.first_name or "",
        "last_name": lead.last_name or "",
        "company": lead.company or "",
        "title": lead.title or "",
        "industry": lead.industry or "",
    }
    return replace_template_vars(template, replacements)


def _campaign_instance_name(campaign: models.Campaign) -> str:
    return campaign.evolution_instance_name or f"user_{campaign.user_id}_whatsapp"


@router.post("/trigger-follow-ups")
def trigger_follow_ups(
    background_tasks: BackgroundTasks,
    x_cron_secret: str = Header(None),
) -> Any:
    """
    Internal endpoint to trigger periodic follow-up checks.
    Usually called by Cloud Scheduler.
    """
    if not settings.CRON_SECRET or x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    
    background_tasks.add_task(check_follow_ups)
    return {"status": "success", "message": "Follow-up check triggered"}


@router.get("/", response_model=List[Dict[str, Any]])
def read_campaigns(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve campaigns with their current performance metrics.
    """
    from sqlalchemy import func, case
    
    campaigns = db.query(models.Campaign).filter(models.Campaign.user_id == current_user.id).offset(skip).limit(limit).all()
    
    result = []
    for campaign in campaigns:
        # Calculate stats for this campaign
        # Use unified Communications table for campaign metrics (covers email, whatsapp, etc.)
        comm_query = db.query(models.Communication).filter(models.Communication.campaign_id == campaign.id)
        total_sent = comm_query.count()
        total_opened = db.query(func.sum(case((models.Communication.opened == True, 1), else_=0))).filter(models.Communication.campaign_id == campaign.id).scalar() or 0
        total_replied = db.query(func.sum(case((models.Communication.replied == True, 1), else_=0))).filter(models.Communication.campaign_id == campaign.id).scalar() or 0
        
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
        
        # Progress calculation (simplified: leads with at least one email sent / total leads)
        total_leads = db.query(models.Lead).filter(models.Lead.user_id == current_user.id).count() # This is a bit rough, ideally we track per-campaign leads
        progress = (total_sent / total_leads * 100) if total_leads > 0 else 0
        
        result.append({
            "id": campaign.id,
            "name": campaign.name,
            "description": campaign.description,
            "channel": campaign.channel,
            "evolution_instance_name": campaign.evolution_instance_name,
            "status": campaign.status,
            "scheduled_for": campaign.scheduled_for,
            "target_industry": campaign.target_industry,
            "daily_send_limit": campaign.daily_send_limit,
            "send_window_start_hour": campaign.send_window_start_hour,
            "send_window_end_hour": campaign.send_window_end_hour,
            "created_at": campaign.created_at,
            "metrics": {
                "sent": total_sent,
                "open_rate": f"{open_rate:.1f}%",
                "reply_rate": f"{reply_rate:.1f}%",
                "progress": min(int(progress), 100)
            }
        })
    
    return result

@router.post("/", response_model=schemas.Campaign)
def create_campaign(
    *,
    db: Session = Depends(deps.get_db),
    campaign_in: schemas.CampaignCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new campaign.
    """
    if campaign_in.channel == "whatsapp" and not campaign_in.evolution_instance_name:
        raise HTTPException(status_code=400, detail="Evolution instance name is required for WhatsApp campaigns")

    # Create campaign
    campaign_data = campaign_in.dict(exclude={"sequences"})
    campaign = models.Campaign(**campaign_data, user_id=current_user.id)
    db.add(campaign)
    db.flush() # Get campaign ID

    # Create sequences
    for i, seq_in in enumerate(campaign_in.sequences):
        sequence_data = seq_in.dict(exclude={"step_number"})
        sequence = models.Sequence(
            **sequence_data,
            campaign_id=campaign.id,
            step_number=i + 1
        )
        db.add(sequence)
    
    db.commit()
    db.refresh(campaign)
    return campaign

@router.get("/{campaign_id}", response_model=schemas.Campaign)
def read_campaign(
    campaign_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve a campaign and its sequences.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.user_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("/{campaign_id}/send-lead/{lead_id}")
def send_campaign_lead_whatsapp(
    *,
    db: Session = Depends(deps.get_db),
    campaign_id: int,
    lead_id: int,
    send_request: schemas.CampaignSendRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send a WhatsApp campaign sequence message to a single lead.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.user_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.channel != "whatsapp":
        raise HTTPException(status_code=400, detail="Campaign is not configured for WhatsApp")

    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.phone:
        raise HTTPException(status_code=400, detail="Lead does not have a phone number")

    sequence = db.query(models.Sequence).filter(models.Sequence.id == send_request.sequence_id, models.Sequence.campaign_id == campaign.id).first()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    body = _render_whatsapp_body(sequence.body, lead)
    if not body.strip():
        raise HTTPException(status_code=400, detail="WhatsApp sequence body is empty")

    instance_name = send_request.instance_name or _campaign_instance_name(campaign)
    whatsapp_service.ensure_instance_sync(instance_name)
    if sequence.mediatype and sequence.media:
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

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send WhatsApp campaign message")

    comm = Communication(
        campaign_id=campaign.id,
        lead_id=lead.id,
        sequence_id=sequence.id,
        channel="whatsapp",
        provider="evolution",
        provider_id=None,
        subject=sequence.subject + (" (Media)" if sequence.media else ""),
        body=body or sequence.caption or "[Media Attachment]",
        status="sent",
        sent_at=datetime.now(timezone.utc)
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)

    return {
        "status": "success",
        "message": "WhatsApp campaign message sent successfully",
        "communication_id": comm.id,
    }


@router.post("/{campaign_id}/sequences", response_model=schemas.Sequence)
def create_sequence(
    *,
    db: Session = Depends(deps.get_db),
    campaign_id: int,
    sequence_in: schemas.SequenceCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new sequence step for a campaign.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.user_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    sequence = models.Sequence(**sequence_in.dict(), campaign_id=campaign_id)
    db.add(sequence)
    db.commit()
    db.refresh(sequence)
    return sequence
@router.post("/{campaign_id}/launch")
def launch_campaign(
    *,
    db: Session = Depends(deps.get_db),
    campaign_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Launch a campaign.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.user_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    scheduled_for = _to_utc(campaign.scheduled_for)
    now = datetime.now(timezone.utc)

    if scheduled_for and scheduled_for > now:
        campaign.scheduled_for = scheduled_for
        campaign.status = "scheduled"
        db.commit()
        # Cron job will pick this up when the time comes
        return {
            "status": "success",
            "message": "Campaign scheduled successfully",
            "scheduled_for": scheduled_for,
        }

    campaign.scheduled_for = None
    db.commit()

    # Trigger background task immediately
    background_tasks.add_task(launch_campaign_task, campaign_id)

    return {"status": "success", "message": "Campaign launch triggered"}


@router.post("/{campaign_id}/send-new-leads")
def send_new_leads(
    *,
    db: Session = Depends(deps.get_db),
    campaign_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Reuse an existing campaign and queue messages only for leads that have not
    yet received this campaign's first message.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.user_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.scheduled_for = None
    if campaign.status != "active":
        campaign.status = "active"
    db.commit()

    background_tasks.add_task(launch_campaign_task, campaign_id)

    return {"status": "success", "message": "Existing campaign triggered for new leads only"}

@router.post("/{campaign_id}/pause")
def pause_campaign(
    *,
    db: Session = Depends(deps.get_db),
    campaign_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Pause an active campaign.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.user_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign.status = "paused"
    db.commit()
    return {"status": "success", "message": "Campaign paused"}

@router.delete("/{campaign_id}")
def delete_campaign(
    *,
    db: Session = Depends(deps.get_db),
    campaign_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a campaign and its associated sequences.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.user_id == current_user.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Delete associated sequences first (SQLAlchemy should handle this if cascade is set, but explicit is safer)
    db.query(models.Sequence).filter(models.Sequence.campaign_id == campaign_id).delete()
    db.delete(campaign)
    db.commit()
    return {"status": "success", "message": "Campaign deleted"}
