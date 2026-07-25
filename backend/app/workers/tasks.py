
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.email_service import email_service
from app.services.ai_service import ai_service
from app.services.csv_service import csv_service
from app.services.whatsapp_service import whatsapp_service
from app.models.lead import Lead
from app.models.campaign import Campaign, Sequence
from app.models.email import Email
from app.models.communication import Communication
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, or_
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo(settings.APP_TIMEZONE)


def _whatsapp_status_for(phone: str | None, is_whatsapp: bool | None = None) -> str:
    if not phone or not phone.strip():
        return "missing"
    if is_whatsapp is True:
        return "valid"
    if is_whatsapp is False:
        return "invalid"
    return "unknown"


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
    sent_today = db.query(Communication).filter(
        Communication.campaign_id == campaign.id,
        Communication.channel == campaign.channel,
        Communication.sent_at.isnot(None),
        Communication.sent_at >= day_start_utc,
        Communication.sent_at < day_end_utc,
    ).count()
    return max(_daily_limit_for(campaign) - sent_today, 0)


def _base_lead_query_for_campaign(db, campaign: Campaign):
    query = db.query(Lead).filter(Lead.user_id == campaign.user_id)
    if campaign.target_industry and campaign.target_industry != "All Industries":
        industries = [industry.strip() for industry in campaign.target_industry.split(",") if industry.strip()]
        if industries:
            query = query.filter(or_(*[Lead.industry.ilike(f"%{industry}%") for industry in industries]))
    return query


def _lead_query_for_campaign(db, campaign: Campaign):
    query = _base_lead_query_for_campaign(db, campaign)
    if campaign.channel == "whatsapp":
        query = query.filter(Lead.phone.isnot(None), Lead.whatsapp_status == "valid")
    else:
        query = query.filter(Lead.email.isnot(None))
    return query


def _campaign_instance_name(campaign: Campaign) -> str:
    return campaign.evolution_instance_name or f"user_{campaign.user_id}_whatsapp"


def _validate_whatsapp_leads(db, leads: list[Lead], instance_name: str) -> None:
    phones = [lead.phone for lead in leads if lead.phone]
    if not phones:
        return

    validation_results = whatsapp_service.check_whatsapp_numbers_sync(instance_name, phones)
    for lead in leads:
        normalized_phone = whatsapp_service._normalize_phone(lead.phone or "")
        is_whatsapp = validation_results.get(normalized_phone) if normalized_phone else None
        lead.whatsapp_status = _whatsapp_status_for(lead.phone, is_whatsapp)
        db.add(lead)
    db.commit()


def _ensure_campaign_whatsapp_validation(db, campaign: Campaign) -> None:
    if campaign.channel != "whatsapp":
        return

    leads_to_validate = _base_lead_query_for_campaign(db, campaign).filter(
        Lead.phone.isnot(None),
        Lead.whatsapp_status == "unknown",
    ).all()

    if not leads_to_validate:
        return

    instance_name = _campaign_instance_name(campaign)
    whatsapp_service.ensure_instance_sync(instance_name)
    _validate_whatsapp_leads(db, leads_to_validate, instance_name)


def _send_campaign_message_task(campaign: Campaign, lead: Lead, sequence: Sequence):
    if campaign.channel == "whatsapp":
        from app.workers.whatsapp_tasks import send_whatsapp_message_task
        print(f"DEBUG: [whatsapp] Queueing campaign {campaign.id} step {sequence.step_number} for lead {lead.id}")
        send_whatsapp_message_task(campaign.id, lead.id, sequence.id)
    else:
        print(f"DEBUG: [email] Queueing campaign {campaign.id} step {sequence.step_number} for lead {lead.id}")
        send_campaign_email_task(campaign.id, lead.id, sequence.id)


def _queue_initial_campaign_messages(db, campaign: Campaign, now_utc: datetime) -> int:
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

    sent_lead_ids = db.query(Communication.lead_id).filter(
        Communication.campaign_id == campaign.id,
        Communication.channel == campaign.channel,
    )
    pending_leads = _lead_query_for_campaign(db, campaign).filter(
        ~Lead.id.in_(sent_lead_ids)
    ).order_by(Lead.id).limit(remaining_capacity).all()

    for lead in pending_leads:
        _send_campaign_message_task(campaign, lead, first_step)

    if pending_leads:
        print(f"DEBUG: [{campaign.channel}] Queued {len(pending_leads)} initial messages for campaign {campaign.id}")
    return len(pending_leads)


def _queue_follow_up_campaign_messages(db, campaign: Campaign, sequences: list[Sequence], now_utc: datetime, remaining_capacity: int) -> int:
    if remaining_capacity <= 0:
        return 0

    if not sequences:
        return 0

    seq_map = {s.step_number: s for s in sequences}
    max_step = max(seq_map.keys())

    latest_messages_sub = db.query(
        Communication.lead_id,
        func.max(Communication.sent_at).label("latest_sent")
    ).filter(
        Communication.campaign_id == campaign.id,
        Communication.channel == campaign.channel,
    ).group_by(Communication.lead_id).subquery()

    latest_messages = db.query(Communication).join(
        latest_messages_sub,
        (Communication.lead_id == latest_messages_sub.c.lead_id) &
        (Communication.sent_at == latest_messages_sub.c.latest_sent)
    ).filter(
        Communication.campaign_id == campaign.id,
        Communication.channel == campaign.channel,
    ).order_by(Communication.sent_at.asc()).all()

    queued = 0
    for last_message in latest_messages:
        if remaining_capacity <= 0:
            break

        has_replied = db.query(Communication).filter(
            Communication.campaign_id == campaign.id,
            Communication.channel == campaign.channel,
            Communication.lead_id == last_message.lead_id,
            Communication.replied == True
        ).first()

        if has_replied:
            print(f"DEBUG: [{campaign.channel}] Skipping follow-up for lead {last_message.lead_id} - lead replied")
            continue

        last_seq = db.query(Sequence).filter(Sequence.id == last_message.sequence_id).first()
        if not last_seq:
            continue

        next_step_num = last_seq.step_number + 1
        if next_step_num > max_step:
            continue

        next_seq = seq_map[next_step_num]
        sent_at_utc = _as_utc(last_message.sent_at)
        if not sent_at_utc:
            continue

        wait_until = sent_at_utc + timedelta(
            days=next_seq.delay_days or 0,
            minutes=next_seq.delay_minutes or 0,
        )
        if now_utc >= wait_until:
            # Avoid queuing duplicate messages for the same sequence and lead
            already_sent = db.query(Communication).filter(
                Communication.campaign_id == campaign.id,
                Communication.channel == campaign.channel,
                Communication.lead_id == last_message.lead_id,
                Communication.sequence_id == next_seq.id,
            ).first()
            if already_sent:
                continue

            print(f"DEBUG: [{campaign.channel}] Time for follow-up: campaign {campaign.id} step {next_step_num} to lead {last_message.lead_id}")
            lead = db.query(Lead).filter(Lead.id == last_message.lead_id).first()
            if lead:
                _send_campaign_message_task(campaign, lead, next_seq)
                remaining_capacity -= 1
                queued += 1

    return queued


def _process_follow_ups(channel: str | None = None) -> None:
    db = SessionLocal()
    try:
        active_campaigns_query = db.query(Campaign).filter(Campaign.status == "active")
        if channel:
            active_campaigns_query = active_campaigns_query.filter(Campaign.channel == channel)

        active_campaigns = active_campaigns_query.all()

        for campaign in active_campaigns:
            now_utc = datetime.now(timezone.utc)

            if not _within_send_window(campaign, now_utc):
                continue

            _queue_initial_campaign_messages(db, campaign, now_utc)
            remaining_capacity = _remaining_daily_capacity(db, campaign, now_utc)
            if remaining_capacity <= 0:
                continue

            sequences = db.query(Sequence).filter(
                Sequence.campaign_id == campaign.id
            ).order_by(Sequence.step_number).all()

            if not sequences:
                continue

            queued = _queue_follow_up_campaign_messages(db, campaign, sequences, now_utc, remaining_capacity)
            if queued:
                remaining_capacity -= queued

    except Exception as e:
        from app.services.audit_service import audit_service
        audit_service.log_error(db, "CAMPAIGN", f"Follow-up engine failed: {str(e)}", e)
        print(f"ERROR in follow-up engine: {str(e)}")
    finally:
        db.close()

def process_csv_import(
    user_id: int,
    file_content: str,
    source: str = "apollo",
    validate_whatsapp: bool = False,
    instance_name: str | None = None,
):
    db = SessionLocal()
    try:
        leads_data = csv_service.parse_csv(file_content, source=source)
        print(f"DEBUG: Parsed {len(leads_data)} leads from CSV")
        
        if not leads_data:
            print(f"DEBUG: No leads parsed from CSV")
            return
            
        added_count = 0
        skipped_count = 0
        seen_emails = set()  # Track emails processed in this import to avoid duplicates within the CSV
        leads_for_validation: list[Lead] = []
        
        for idx, data in enumerate(leads_data):
            email = data.get("email")
            phone = data.get("phone")

            if not email and not phone:
                print(f"DEBUG: Skipping lead {idx} - missing both email and phone")
                skipped_count += 1
                continue
            
            # Deduplicate within this CSV file using phone or valid email
            dup_key = None
            if phone:
                dup_key = f"phone:{phone.strip()}"
            elif email and "@" in email:
                dup_key = f"email:{email.strip().lower()}"
            else:
                dup_key = f"raw:{email}-{data.get('store_name') or data.get('company')}"

            if dup_key in seen_emails:
                print(f"DEBUG: Skipping lead {idx} ({dup_key}) - duplicate in CSV")
                skipped_count += 1
                continue
            seen_emails.add(dup_key)
                
            try:
                # Check if lead exists for this user by phone first, then email
                existing = None
                if phone:
                    existing = db.query(Lead).filter(Lead.phone == phone, Lead.user_id == user_id).first()
                if not existing and email and "@" in email:
                    existing = db.query(Lead).filter(Lead.email == email, Lead.user_id == user_id).first()
                
                if not existing:
                    # Create new lead with only valid fields
                    lead_kwargs = {
                        "first_name": data.get("first_name"),
                        "last_name": data.get("last_name"),
                        "email": email,
                        "phone": phone,
                        "whatsapp_status": _whatsapp_status_for(phone),
                        "company": data.get("company"),
                        "title": data.get("title"),
                        "industry": data.get("industry"),
                        "linkedin_url": data.get("linkedin_url"),
                        "website": data.get("website"),
                        "store_name": data.get("store_name"),
                        "city_area": data.get("city_area"),
                        "address": data.get("address"),
                        "notes": data.get("notes"),
                        "user_id": user_id,
                    }
                    lead = Lead(**lead_kwargs)
                    db.add(lead)
                    if validate_whatsapp and lead.phone:
                        leads_for_validation.append(lead)
                    print(f"DEBUG: Added lead: {dup_key}")
                    added_count += 1
                else:
                    # Update existing lead with missing data
                    updated = False
                    fields_to_update = ["first_name", "last_name", "company", "title", "industry", "linkedin_url", "website", "phone", "email", "store_name", "city_area", "address", "notes"]
                    for key in fields_to_update:
                        if data.get(key) and not getattr(existing, key, None):
                            setattr(existing, key, data[key])
                            if key == "phone":
                                existing.whatsapp_status = _whatsapp_status_for(existing.phone)
                            updated = True
                    if validate_whatsapp and existing.phone:
                        leads_for_validation.append(existing)
                    if updated:
                        print(f"DEBUG: Updated existing lead with new info: {dup_key}")
                    else:
                        print(f"DEBUG: Lead already exists and is up to date: {dup_key}")
            except Exception as lead_error:
                print(f"DEBUG: Error processing lead {idx} ({dup_key}): {str(lead_error)}")
                # Try to rollback this single transaction to continue with others
                try:
                    db.rollback()
                except Exception:
                    pass
                skipped_count += 1
                continue
                
        db.commit()

        if validate_whatsapp and instance_name:
            whatsapp_service.ensure_instance_sync(instance_name)
            _validate_whatsapp_leads(db, leads_for_validation, instance_name)
        print(f"DEBUG: Successfully committed - Added: {added_count}, Skipped: {skipped_count}")
    except Exception as e:
        from app.services.audit_service import audit_service
        print(f"DEBUG: Error processing CSV: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        # Try to rollback before logging error
        try:
            db.rollback()
        except Exception:
            pass
        # Use a fresh database session for logging to avoid PendingRollbackError
        try:
            audit_service.log_error(db, "CSV_IMPORT", f"Failed to process CSV for user {user_id}", e)
        except Exception as log_error:
            print(f"DEBUG: Failed to log error: {str(log_error)}")
    finally:
        try:
            db.close()
        except Exception:
            pass

import asyncio

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

def send_campaign_email_task(campaign_id: int, lead_id: int, sequence_id: int):
    db = SessionLocal()
    try:
        import asyncio
        asyncio.run(email_service.send_cold_email(db, campaign_id, lead_id, sequence_id))
    finally:
        db.close()

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
        _ensure_campaign_whatsapp_validation(db, campaign)
        matched_leads = _lead_query_for_campaign(db, campaign).count()
        queued = _queue_initial_campaign_messages(db, campaign, now_utc)
        print(f"DEBUG: Activated [{campaign.channel}] campaign '{campaign.name}' ({campaign.id}) for {matched_leads} leads, queued {queued} initial messages")
            
    except Exception as e:
        from app.services.audit_service import audit_service
        audit_service.log_error(db, "CAMPAIGN", f"Failed to launch campaign {campaign_id}", e)
        print(f"ERROR launching campaign: {str(e)}")
    finally:
        db.close()

def check_follow_ups():
    """
    Periodic task to check which leads need a follow-up,
    and launch any campaigns that are scheduled for now.
    """
    # 1. Launch Scheduled Campaigns
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        scheduled_campaigns = db.query(Campaign).filter(
            Campaign.status == "scheduled",
            Campaign.scheduled_for <= now_utc
        ).all()
        for campaign in scheduled_campaigns:
            print(f"DEBUG: Auto-launching scheduled campaign {campaign.id}")
            launch_campaign_task(campaign.id)
    finally:
        db.close()

    # 2. Process Follow-ups
    _process_follow_ups()


def check_whatsapp_follow_ups():
    """
    Periodic task to check only WhatsApp campaign follow-ups.
    """
    _process_follow_ups("whatsapp")
