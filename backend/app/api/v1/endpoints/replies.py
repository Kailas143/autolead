from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, models
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.Reply])
def read_replies(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve replies for leads belonging to the current user.
    """
    replies = (
        db.query(models.Reply)
        .join(models.Lead)
        .filter(models.Lead.user_id == current_user.id)
        .order_by(models.Reply.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return replies
