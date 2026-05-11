from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.lead import Lead
from app.models.email import Email

router = APIRouter()

@router.get("/stats")
def get_analytics_stats(
    db: Session = Depends(get_db),
) -> Any:
    """
    Get analytics statistics.
    """
    total_leads = db.query(func.count(Lead.id)).scalar() or 0
    total_emails_sent = db.query(func.count(Email.id)).scalar() or 0
    total_opens = db.query(func.count(Email.id)).filter(Email.opened == True).scalar() or 0
    total_clicks = db.query(func.count(Email.id)).filter(Email.clicked == True).scalar() or 0
    total_replies = db.query(func.count(Email.id)).filter(Email.replied == True).scalar() or 0
    
    reply_rate = (total_replies / total_emails_sent * 100) if total_emails_sent > 0 else 0
    open_rate = (total_opens / total_emails_sent * 100) if total_emails_sent > 0 else 0

    return {
        "total_leads": total_leads,
        "total_emails_sent": total_emails_sent,
        "total_opens": total_opens,
        "open_rate": f"{open_rate:.1f}%",
        "total_clicks": total_clicks,
        "total_replies": total_replies,
        "reply_rate": f"{reply_rate:.1f}%"
    }