from app.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.email_service import email_service
from app.services.ai_service import ai_service
from app.services.csv_service import csv_service
from app.models.lead import Lead
from app.models.campaign import Campaign, Sequence
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
        print(f"DEBUG: Error processing CSV: {str(e)}")
        db.rollback()
    finally:
        db.close()

@celery_app.task
def generate_ai_lines_task(lead_id: int):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            # Generate personalized line
            ai_line = ai_service.generate_personalization({
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "title": lead.title,
                "industry": lead.industry
            })
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
            # 2. Find all sequences for this campaign
            sequences = db.query(Sequence).filter(Sequence.campaign_id == campaign.id).order_by(Sequence.step_number).all()
            
            # 3. For each lead in this campaign
            # (Note: In a large system, we'd use an EmailTracking table to see where they are)
            # For now, let's keep it simple
            pass
    finally:
        db.close()
