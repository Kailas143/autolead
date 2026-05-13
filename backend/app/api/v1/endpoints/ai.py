from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.services.ai_service import ai_service
from app.api import deps
from app import models

router = APIRouter()

@router.post("/generate-followup")
async def generate_followup(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    lead_data: Dict[str, Any],
) -> Any:
    """
    Generate an AI-powered follow-up email.
    """
    try:
        content = await ai_service.generate_followup(lead_data, db=db, user_id=current_user.id)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-subject")
async def generate_subject(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    company: str,
    industry: str
) -> Any:
    """
    Generate AI-powered subject lines.
    """
    try:
        subjects = await ai_service.generate_subject_lines(company, industry, db=db, user_id=current_user.id)
        return {"subjects": subjects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
