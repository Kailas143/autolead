from typing import Any
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.api import deps
from app.models.lead import Lead
from app.models.email import Email
from app.models.reply import Reply
from app.models.campaign import Sequence, Campaign
from datetime import datetime, timedelta
import pytz

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
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    for i in range(6, -1, -1):
        # Use local time for day boundaries
        day = (now_ist - timedelta(days=i)).date()
        # Use func.date for more reliable date comparison in Postgres/SQLite
        day_query = email_query.filter(func.date(Email.sent_at) == day)
        sent_count = day_query.count()
        open_count = day_query.filter(Email.opened == True).count()
        last_7_days.append({
            "date": day.strftime("%b %d"),
            "sent": sent_count,
            "opens": open_count
        })

    # 4. Top Performing Sequences
    top_sequences = db.query(
        Sequence.subject,
        func.count(Email.id).label("sent_count"),
        func.sum(case((Email.opened == True, 1), else_=0)).label("open_count"),
        func.sum(case((Email.replied == True, 1), else_=0)).label("reply_count")
    ).join(Email, Email.sequence_id == Sequence.id).join(Lead).filter(
        Lead.user_id == current_user.id
    ).group_by(Sequence.id, Sequence.subject).order_by(func.count(Email.id).desc()).limit(5).all()

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

@router.get("/outreach-log")
def get_outreach_log(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get detailed outreach history for each lead.
    """
    leads = db.query(Lead).filter(Lead.user_id == current_user.id).all()
    
    log = []
    for lead in leads:
        # Get all emails sent to this lead, joined with sequence to get step numbers
        emails = db.query(Email, Sequence.step_number).join(
            Sequence, Email.sequence_id == Sequence.id
        ).filter(Email.lead_id == lead.id).order_by(Email.sent_at.asc()).all()
        
        log.append({
            "id": lead.id,
            "lead_name": f"{lead.first_name} {lead.last_name}",
            "company": lead.company,
            "email": lead.email,
            "industry": lead.industry,
            "emails_sent": len(emails),
            "last_step": emails[-1][1] if emails else 0,
            "last_sent": emails[-1][0].sent_at if emails else None,
            "status": "replied" if any(e[0].replied for e in emails) else ("active" if emails else "pending")
        })
    
    return log


@router.get("/sent-messages")
def get_sent_messages(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all sent messages for the current user with customer and send-time details.
    """
    messages = (
        db.query(Email, Lead, Sequence, Campaign)
        .join(Lead, Email.lead_id == Lead.id)
        .join(Sequence, Email.sequence_id == Sequence.id)
        .join(Campaign, Email.campaign_id == Campaign.id)
        .filter(Lead.user_id == current_user.id)
        .order_by(Email.sent_at.desc(), Email.created_at.desc())
        .all()
    )

    sent_messages = []
    for email, lead, sequence, campaign in messages:
        customer_name = " ".join(part for part in [lead.first_name, lead.last_name] if part).strip() or lead.email
        status = "replied" if email.replied else "opened" if email.opened else "sent"
        body_preview = (email.body or "").strip().replace("\n", " ")

        sent_messages.append({
            "id": email.id,
            "customer_name": customer_name,
            "customer_email": lead.email,
            "company": lead.company,
            "industry": lead.industry,
            "subject": email.subject,
            "body_preview": body_preview[:160],
            "sent_at": email.sent_at or email.created_at,
            "campaign_name": campaign.name,
            "sequence_step": sequence.step_number,
            "status": status,
        })

    return {
        "summary": {
            "total_messages": len(sent_messages),
            "total_customers": len({message["customer_email"] for message in sent_messages}),
            "latest_sent_at": sent_messages[0]["sent_at"] if sent_messages else None,
        },
        "messages": sent_messages,
    }
