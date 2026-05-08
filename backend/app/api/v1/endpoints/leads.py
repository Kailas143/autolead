from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app import schemas, models
from app.api import deps
from app.services.csv_service import csv_service
from app.workers.tasks import process_csv_import

router = APIRouter()

@router.get("/", response_model=List[schemas.Lead])
def read_leads(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve leads belonging to the current user.
    """
    leads = db.query(models.Lead).filter(models.Lead.user_id == current_user.id).offset(skip).limit(limit).all()
    return leads

@router.post("/upload")
async def upload_leads(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload leads via CSV.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    content = await file.read()
    try:
        # Decode to string for JSON serialization in Celery
        content_str = content.decode("utf-8")
        process_csv_import.delay(current_user.id, content_str)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a UTF-8 CSV.")
    
    return {"message": "CSV upload started in background"}

@router.get("/{lead_id}", response_model=schemas.Lead)
def read_lead_by_id(
    lead_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get lead by ID.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead