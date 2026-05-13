from datetime import datetime, timezone
from typing import Any, List, Dict
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app import schemas, models
from app.api import deps
from app.workers.tasks import launch_campaign_task, check_follow_ups
from app.core.config import settings
from fastapi import Header

router = APIRouter()


def _to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

@router.post("/trigger-follow-ups")
def trigger_follow_ups(
    x_cron_secret: str = Header(None),
) -> Any:
    """
    Internal endpoint to trigger periodic follow-up checks.
    Usually called by Cloud Scheduler.
    """
    if not settings.CRON_SECRET or x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    
    check_follow_ups.delay()
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
        email_query = db.query(models.Email).filter(models.Email.campaign_id == campaign.id)
        total_sent = email_query.count()
        
        # Use portable case() syntax for SQLAlchemy 2.0
        total_opened = db.query(func.sum(case((models.Email.opened == True, 1), else_=0))).filter(models.Email.campaign_id == campaign.id).scalar() or 0
        total_replied = db.query(func.sum(case((models.Email.replied == True, 1), else_=0))).filter(models.Email.campaign_id == campaign.id).scalar() or 0
        
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
        
        # Progress calculation (simplified: leads with at least one email sent / total leads)
        total_leads = db.query(models.Lead).filter(models.Lead.user_id == current_user.id).count() # This is a bit rough, ideally we track per-campaign leads
        progress = (total_sent / total_leads * 100) if total_leads > 0 else 0
        
        result.append({
            "id": campaign.id,
            "name": campaign.name,
            "description": campaign.description,
            "status": campaign.status,
            "scheduled_for": campaign.scheduled_for,
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
        campaign.status = "scheduled"
        db.commit()
        launch_campaign_task.apply_async(args=[campaign_id], eta=scheduled_for)
        return {
            "status": "success",
            "message": "Campaign scheduled successfully",
            "scheduled_for": scheduled_for,
        }

    campaign.scheduled_for = None
    db.commit()

    # Trigger background task immediately
    launch_campaign_task.delay(campaign_id)

    return {"status": "success", "message": "Campaign launch triggered"}

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
