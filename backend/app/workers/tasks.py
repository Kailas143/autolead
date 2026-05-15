from app.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.email_service import email_service
from app.services.ai_service import ai_service
from app.services.csv_service import csv_service
from app.models.lead import Lead
from app.models.campaign import Campaign, Sequence
from app.models.email import Email
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, or_
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo(settings.APP_TIMEZONE)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _daily_limit_for(campaign: Campaign) -> int:
    return max(campaign.daily_send_limit or 50, 1)


def _window_hours_for(campaign: Campaign) -> tuple[int, int]:
    start = max(0, min(23, campaign.send_window_start_hour if campaign.send_window_start_hour is not None else 9))
    end = max(0, min(23, campaign.send_window_end_hour if campaign.send_window_end_hour is not None else 17))
    return start, end


def _within_send_window(campaign: Campaign, now_utc: datetime) -> bool:
    start_hour, end_hour = _window_hours_for(campaign)
    if start_hour == end_hour:
        return True

    local_hour = now_utc.astimezone(APP_TZ).hour
    if start_hour < end_hour:
        return start_hour <= local_hour < end_hour
    return local_hour >= start_hour or local_hour < end_hour


def _local_day_bounds_utc(now_utc: datetime) -> tuple[datetime, datetime]:
    local_now = now_utc.astimezone(APP_TZ)
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    local_end = local_start + timedelta(days=1)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def _remaining_daily_capacity(db, campaign: Campaign, now_utc: datetime) -> int:
    day_start_utc, day_end_utc = _local_day_bounds_utc(now_utc)
    sent_today = db.query(Email).filter(
        Email.campaign_id == campaign.id,
        Email.sent_at.isnot(None),
        Email.sent_at >= day_start_utc,
        Email.sent_at < day_end_utc,
    ).count()
    return max(_daily_limit_for(campaign) - sent_today, 0)


def _lead_query_for_campaign(db, campaign: Campaign):
    query = db.query(Lead).filter(Lead.user_id == campaign.user_id)
    if campaign.target_industry and campaign.target_industry != "All Industries":
        industries = [industry.strip() for industry in campaign.target_industry.split(",") if industry.strip()]
        if industries:
            query = query.filter(or_(*[Lead.industry.ilike(f"%{industry}%") for industry in industries]))
    return query


def _queue_initial_campaign_emails(db, campaign: Campaign, now_utc: datetime) -> int:
    if not _within_send_window(campaign, now_utc):
        return 0

    remaining_capacity = _remaining_daily_capacity(db, campaign, now_utc)
    if remaining_capacity <= 0:
        return 0

    first_step = db.query(Sequence).filter(
        Sequence.campaign_id == campaign.id,
        Sequence.step_number == 1
    ).first()
    if not first_step:
        print(f"ERROR: No sequence steps found for campaign {campaign.id}")
        return 0

    sent_lead_ids = db.query(Email.lead_id).filter(Email.campaign_id == campaign.id)
    pending_leads = _lead_query_for_campaign(db, campaign).filter(
        ~Lead.id.in_(sent_lead_ids)
    ).order_by(Lead.id).limit(remaining_capacity).all()

    for lead in pending_leads:
        send_campaign_email_task.delay(campaign.id, lead.id, first_step.id)

    if pending_leads:
        print(f"DEBUG: Queued {len(pending_leads)} initial emails for campaign {campaign.id}")
    return len(pending_leads)

@celery_app.task
def process_csv_import(user_id: int, file_content: str):
    db = SessionLocal()
    try:
        leads_data = csv_service.parse_apollo_csv(file_content)
        print(f"DEBUG: Parsed {len(leads_data)} leads from CSV")
        for data in leads_data:
            email = data.get("email")
            if not email:
                print(f"DEBUG: Skipping lead missing email: {data.get('first_name', 'Unknown')}")
                continue
                
            # Check if lead exists
            existing = db.query(Lead).filter(Lead.email == email).first()
            if not existing:
                lead = Lead(**data, user_id=user_id)
                db.add(lead)
                print(f"DEBUG: Added lead: {email}")
            else:
                # Update existing lead with missing data
                updated = False
                for key, value in data.items():
                    if value and not getattr(existing, key, None):
                        setattr(existing, key, value)
                        updated = True
                if updated:
                    print(f"DEBUG: Updated existing lead with new info: {email}")
                else:
                    print(f"DEBUG: Lead already exists and is up to date: {email}")
        db.commit()
        print(f"DEBUG: Successfully committed leads to database")
    except Exception as e:
        from app.services.audit_service import audit_service
        audit_service.log_error(db, "CSV_IMPORT", f"Failed to process CSV for user {user_id}", e)
        print(f"DEBUG: Error processing CSV: {str(e)}")
        db.rollback()
    finally:
        db.close()

import asyncio

@celery_app.task
def generate_ai_lines_task(lead_id: int):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            # Generate personalized line
            ai_line = asyncio.run(ai_service.generate_personalization({
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "title": lead.title,
                "industry": lead.industry
            }, db=db, user_id=lead.user_id))
            # For now, let's just log it or store it in a new column
            # In a real app, you'd have a lead_personalization table
            print(f"Generated AI Line for {lead.email}: {ai_line}")
    finally:
        db.close()

@celery_app.task
def send_campaign_email_task(campaign_id: int, lead_id: int, sequence_id: int):
    db = SessionLocal()
    try:
        import asyncio
        asyncio.run(email_service.send_cold_email(db, campaign_id, lead_id, sequence_id))
    finally:
        db.close()

@celery_app.task
def launch_campaign_task(campaign_id: int):
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            print(f"ERROR: Campaign {campaign_id} not found")
            return

        if campaign.status == "paused":
            print(f"DEBUG: Skipping launch for paused campaign {campaign_id}")
            return

        if campaign.scheduled_for:
            scheduled_for = _as_utc(campaign.scheduled_for)

            if scheduled_for and scheduled_for > now_utc:
                print(f"DEBUG: Campaign {campaign_id} scheduled for later at {scheduled_for.isoformat()}")
                return

        # Update campaign status
        campaign.status = "active"
        campaign.scheduled_for = None
        db.commit()
        matched_leads = _lead_query_for_campaign(db, campaign).count()
        queued = _queue_initial_campaign_emails(db, campaign, now_utc)
        print(f"DEBUG: Activated campaign '{campaign.name}' for {matched_leads} leads, queued {queued} initial emails")
            
    except Exception as e:
        from app.services.audit_service import audit_service
        audit_service.log_error(db, "CAMPAIGN", f"Failed to launch campaign {campaign_id}", e)
        print(f"ERROR launching campaign: {str(e)}")
    finally:
        db.close()

@celery_app.task
def check_follow_ups():
    """
    Periodic task to check which leads need a follow-up.
    """
    db = SessionLocal()
    try:
        # 1. Find all active campaigns
        active_campaigns = db.query(Campaign).filter(Campaign.status == "active").all()
        
        for campaign in active_campaigns:
            now_utc = datetime.now(timezone.utc)

            if not _within_send_window(campaign, now_utc):
                continue

            _queue_initial_campaign_emails(db, campaign, now_utc)
            remaining_capacity = _remaining_daily_capacity(db, campaign, now_utc)
            if remaining_capacity <= 0:
                continue

            # 2. Get all sequences for this campaign ordered by step
            sequences = db.query(Sequence).filter(
                Sequence.campaign_id == campaign.id
            ).order_by(Sequence.step_number).all()
            
            if not sequences:
                continue

            # Create a map of step_number -> sequence for easy lookup
            seq_map = {s.step_number: s for s in sequences}
            max_step = max(seq_map.keys())

            # 3. Find all leads that have received at least one email in this campaign
            # We group by lead_id and get the latest email
            latest_emails_sub = db.query(
                Email.lead_id,
                func.max(Email.sent_at).label("latest_sent")
            ).filter(Email.campaign_id == campaign.id).group_by(Email.lead_id).subquery()

            latest_emails = db.query(Email).join(
                latest_emails_sub,
                (Email.lead_id == latest_emails_sub.c.lead_id) & 
                (Email.sent_at == latest_emails_sub.c.latest_sent)
            ).order_by(Email.sent_at.asc()).all()

            for last_email in latest_emails:
                if remaining_capacity <= 0:
                    break

                # 4. SKIP if lead has replied
                # Check if ANY email to this lead in this campaign has 'replied' = True
                has_replied = db.query(Email).filter(
                    Email.campaign_id == campaign.id,
                    Email.lead_id == last_email.lead_id,
                    Email.replied == True
                ).first()

                if has_replied:
                    print(f"DEBUG: Skipping follow-up for {last_email.lead_id} - Lead Replied!")
                    continue

                # 5. Check if there is a next step
                last_seq = db.query(Sequence).filter(Sequence.id == last_email.sequence_id).first()
                if not last_seq:
                    continue

                next_step_num = last_seq.step_number + 1
                if next_step_num > max_step:
                    # Campaign finished for this lead
                    continue

                next_seq = seq_map[next_step_num]
                
                # 6. Check if it's time to send (Production: days)
                sent_at_utc = _as_utc(last_email.sent_at)
                if not sent_at_utc:
                    continue

                wait_until = sent_at_utc + timedelta(days=next_seq.delay_days)
                if now_utc >= wait_until:
                    print(f"DEBUG: Time for follow-up! Sending Step {next_step_num} to lead {last_email.lead_id}")
                    send_campaign_email_task.delay(campaign.id, last_email.lead_id, next_seq.id)
                    remaining_capacity -= 1

    except Exception as e:
        from app.services.audit_service import audit_service
        audit_service.log_error(db, "CAMPAIGN", f"Follow-up engine failed: {str(e)}", e)
        print(f"ERROR in follow-up engine: {str(e)}")
    finally:
        db.close()
