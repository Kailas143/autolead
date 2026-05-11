from typing import Any, List
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app import schemas, models
from app.api import deps
from app.workers.tasks import launch_campaign_task

router = APIRouter()

@router.get("/", response_model=List[schemas.Campaign])
def read_campaigns(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve campaigns.
    """
    campaigns = db.query(models.Campaign).filter(models.Campaign.user_id == current_user.id).offset(skip).limit(limit).all()
    return campaigns

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
    
    # Trigger background task
    launch_campaign_task.delay(campaign_id)
    
    return {"status": "success", "message": "Campaign launch triggered"}
