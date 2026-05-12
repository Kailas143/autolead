from typing import Any, List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from app.api import deps
from app.models.lead import Lead
from app.models.email import Email
from app.models.reply import Reply
from app.models.campaign import Sequence
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/stats")
def get_analytics_stats(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get comprehensive analytics statistics for the current user.
    """
    # 1. Base Metrics
    total_leads = db.query(func.count(Lead.id)).filter(Lead.user_id == current_user.id).scalar() or 0
    
    email_query = db.query(Email).join(Lead).filter(Lead.user_id == current_user.id)
    total_emails_sent = email_query.count()
    total_opens = email_query.filter(Email.opened == True).count()
    total_replies = email_query.filter(Email.replied == True).count()
    
    reply_rate = (total_replies / total_emails_sent * 100) if total_emails_sent > 0 else 0
    open_rate = (total_opens / total_emails_sent * 100) if total_emails_sent > 0 else 0

    # 2. Reply Sentiment (for Pie Chart)
    sentiment_stats = db.query(
        Reply.classification, 
        func.count(Reply.id)
    ).join(Lead).filter(Lead.user_id == current_user.id).group_by(Reply.classification).all()
    
    sentiment_data = [{"name": s[0], "value": s[1]} for s in sentiment_stats]

    # 3. Engagement Over Time (last 7 days)
    last_7_days = []
    for i in range(6, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        sent_count = email_query.filter(cast(Email.sent_at, Date) == day).count()
        open_count = email_query.filter(cast(Email.sent_at, Date) == day, Email.opened == True).count()
        last_7_days.append({
            "date": day.strftime("%b %d"),
            "sent": sent_count,
            "opens": open_count
        })

    # 4. Top Performing Sequences
    top_sequences = db.query(
        Sequence.subject,
        func.count(Email.id).label("sent_count"),
        func.sum(cast(Email.opened, func.Integer)).label("open_count"),
        func.sum(cast(Email.replied, func.Integer)).label("reply_count")
    ).join(Email, Email.sequence_id == Sequence.id).join(Lead).filter(
        Lead.user_id == current_user.id
    ).group_by(Sequence.id).order_by(func.count(Email.id).desc()).limit(5).all()

    formatted_sequences = [
        {
            "subject": s[0],
            "sent": s[1],
            "opens": s[2],
            "replies": s[3],
            "reply_rate": f"{(s[3] / s[1] * 100):.1f}%" if s[1] > 0 else "0%"
        } for s in top_sequences
    ]

    return {
        "summary": {
            "total_leads": total_leads,
            "total_emails_sent": total_emails_sent,
            "total_opens": total_opens,
            "open_rate": f"{open_rate:.1f}%",
            "total_replies": total_replies,
            "reply_rate": f"{reply_rate:.1f}%"
        },
        "sentiment": sentiment_data,
        "engagement": last_7_days,
        "top_sequences": formatted_sequences
    }