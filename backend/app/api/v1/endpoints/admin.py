from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models
from app.api import deps

router = APIRouter()

from fastapi.encoders import jsonable_encoder

@router.get("/logs", response_model=List[Dict[str, Any]])
def get_system_logs(
    db: Session = Depends(deps.get_db),
    limit: int = 50,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve recent system logs.
    """
    logs = db.query(models.SystemLog).order_by(models.SystemLog.created_at.desc()).limit(limit).all()
    return jsonable_encoder(logs)

@router.get("/ai-usage", response_model=Dict[str, Any])
def get_ai_usage_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve AI token usage statistics.
    """
    total_tokens = db.query(func.sum(models.AIUsage.total_tokens)).scalar() or 0
    total_prompt = db.query(func.sum(models.AIUsage.prompt_tokens)).scalar() or 0
    total_completion = db.query(func.sum(models.AIUsage.completion_tokens)).scalar() or 0
    
    usage_by_task = db.query(
        models.AIUsage.task_type,
        func.sum(models.AIUsage.total_tokens).label("tokens")
    ).group_by(models.AIUsage.task_type).all()
    
    recent_usage = db.query(models.AIUsage).order_by(models.AIUsage.created_at.desc()).limit(20).all()
    
    return jsonable_encoder({
        "totals": {
            "total": total_tokens,
            "prompt": total_prompt,
            "completion": total_completion
        },
        "by_task": {task: tokens for task, tokens in usage_by_task},
        "recent": recent_usage
    })

@router.delete("/logs/clear")
def clear_logs(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Clear all system logs.
    """
    db.query(models.SystemLog).delete()
    db.commit()
    return {"message": "Logs cleared"}
