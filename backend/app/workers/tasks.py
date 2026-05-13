from app.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.email_service import email_service
from app.services.ai_service import ai_service
from app.services.csv_service import csv_service
from app.models.lead import Lead
from app.models.campaign import Campaign, Sequence
from app.models.email import Email
from datetime import datetime, timedelta

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
        email_service.send_cold_email(db, campaign_id, lead_id, sequence_id)
    finally:
        db.close()

@celery_app.task
def launch_campaign_task(campaign_id: int):
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            print(f"ERROR: Campaign {campaign_id} not found")
            return
            
        # Update campaign status
        campaign.status = "active"
        db.commit()
            
        # Find first sequence step
        first_step = db.query(Sequence).filter(
            Sequence.campaign_id == campaign_id,
            Sequence.step_number == 1
        ).first()
        
        if not first_step:
            print(f"ERROR: No sequence steps found for campaign {campaign_id}")
            return
            
        # Find matching leads
        query = db.query(Lead).filter(Lead.user_id == campaign.user_id)
        if campaign.target_industry and campaign.target_industry != "All Industries":
            # Using ilike for case-insensitive matching
            query = query.filter(Lead.industry.ilike(f"%{campaign.target_industry}%"))
            
        leads = query.all()
        print(f"DEBUG: Launching campaign '{campaign.name}' for {len(leads)} leads")
        
        for lead in leads:
            # Send the first email
            send_campaign_email_task.delay(campaign.id, lead.id, first_step.id)
            
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
            from sqlalchemy import func
            latest_emails_sub = db.query(
                Email.lead_id,
                func.max(Email.sent_at).label("latest_sent")
            ).filter(Email.campaign_id == campaign.id).group_by(Email.lead_id).subquery()

            latest_emails = db.query(Email).join(
                latest_emails_sub,
                (Email.lead_id == latest_emails_sub.c.lead_id) & 
                (Email.sent_at == latest_emails_sub.c.latest_sent)
            ).all()

            for last_email in latest_emails:
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
                wait_until = last_email.sent_at + timedelta(days=next_seq.delay_days)
                if datetime.utcnow() >= wait_until.replace(tzinfo=None):
                    print(f"DEBUG: Time for follow-up! Sending Step {next_step_num} to lead {last_email.lead_id}")
                    send_campaign_email_task.delay(campaign.id, last_email.lead_id, next_seq.id)

    except Exception as e:
        from app.services.audit_service import audit_service
        audit_service.log_error(db, "CAMPAIGN", f"Follow-up engine failed: {str(e)}", e)
        print(f"ERROR in follow-up engine: {str(e)}")
    finally:
        db.close()
