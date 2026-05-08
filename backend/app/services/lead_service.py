from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate


def get_by_id(db: Session, *, id: int) -> Optional[Lead]:
    return db.query(Lead).filter(Lead.id == id).first()


def get_by_email(db: Session, *, email: str) -> Optional[Lead]:
    return db.query(Lead).filter(Lead.email == email).first()


def get_multi(db: Session, *, skip: int = 0, limit: int = 100) -> List[Lead]:
    return db.query(Lead).offset(skip).limit(limit).all()


def create(db: Session, *, obj_in: LeadCreate) -> Lead:
    db_obj = Lead(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, *, db_obj: Lead, obj_in: LeadUpdate) -> Lead:
    update_data = obj_in.dict(exclude_unset=True)
    for field in update_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove(db: Session, *, id: int) -> Lead:
    obj = db.query(Lead).get(id)
    db.delete(obj)
    db.commit()
    return obj