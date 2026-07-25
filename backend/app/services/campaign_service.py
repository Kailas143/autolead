from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.campaign import Campaign, Sequence
from app.schemas.campaign import CampaignCreate, CampaignUpdate, SequenceCreate


def get_by_id(db: Session, *, id: int) -> Optional[Campaign]:
    return db.query(Campaign).filter(Campaign.id == id).first()


def get_multi_by_user(db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Campaign]:
    return db.query(Campaign).filter(Campaign.user_id == user_id).offset(skip).limit(limit).all()


def create(db: Session, *, obj_in: CampaignCreate, user_id: int) -> Campaign:
    db_obj = Campaign(
        name=obj_in.name,
        description=obj_in.description,
        channel=obj_in.channel,
        evolution_instance_name=obj_in.evolution_instance_name,
        user_id=user_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    # Create sequences
    for seq_data in obj_in.sequences:
        seq = Sequence(
            campaign_id=db_obj.id,
            step_number=seq_data.step_number,
            subject=seq_data.subject,
            body=seq_data.body,
            delay_days=seq_data.delay_days,
            delay_minutes=seq_data.delay_minutes,
        )
        db.add(seq)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, *, db_obj: Campaign, obj_in: CampaignUpdate) -> Campaign:
    update_data = obj_in.dict(exclude_unset=True)
    for field in update_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove(db: Session, *, id: int) -> Campaign:
    obj = db.query(Campaign).get(id)
    db.delete(obj)
    db.commit()
    return obj
