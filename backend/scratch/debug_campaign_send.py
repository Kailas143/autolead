#!/usr/bin/env python3
"""
Debug script to diagnose campaign email sending issues.
"""
import sys
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# Add the backend directory to the path
sys.path.insert(0, '/home/dell/autolead/backend')

from app.core.database import SessionLocal
from app.models.campaign import Campaign, Sequence
from app.models.lead import Lead
from app.models.email import Email
from app.core.config import settings
from sqlalchemy import or_

db = SessionLocal()

try:
    print("=" * 80)
    print("CAMPAIGN EMAIL DEBUGGING")
    print("=" * 80)
    
    # Get all active campaigns
    campaigns = db.query(Campaign).filter(Campaign.status == "active").all()
    print(f"\n✓ Found {len(campaigns)} active campaigns")
    
    for campaign in campaigns:
        print(f"\n{'─' * 80}")
        print(f"Campaign: {campaign.name} (ID: {campaign.id})")
        print(f"Status: {campaign.status}")
        print(f"Target Industry: {campaign.target_industry or 'All Industries'}")
        print(f"Daily Limit: {campaign.daily_send_limit}")
        print(f"Send Window: {campaign.send_window_start_hour}:00 - {campaign.send_window_end_hour}:00")
        
        # Check current time vs send window
        APP_TZ = ZoneInfo(settings.APP_TIMEZONE)
        now_utc = datetime.now(timezone.utc)
        local_now = now_utc.astimezone(APP_TZ)
        local_hour = local_now.hour
        
        start_hour = max(0, min(23, campaign.send_window_start_hour if campaign.send_window_start_hour is not None else 9))
        end_hour = max(0, min(23, campaign.send_window_end_hour if campaign.send_window_end_hour is not None else 17))
        
        print(f"Local time: {local_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Current hour: {local_hour}")
        
        # Check if within send window
        if start_hour < end_hour:
            within_window = start_hour <= local_hour < end_hour
        else:
            within_window = local_hour >= start_hour or local_hour < end_hour
        
        print(f"Within send window: {'✓ YES' if within_window else '✗ NO'}")
        
        # Check for sequences
        sequences = db.query(Sequence).filter(Sequence.campaign_id == campaign.id).all()
        print(f"Sequences: {len(sequences)}")
        for seq in sorted(sequences, key=lambda s: s.step_number):
            print(f"  - Step {seq.step_number}: {seq.subject}")
        
        if not sequences:
            print(f"  ⚠️  WARNING: No sequences found!")
            continue
        
        # Check for matching leads
        query = db.query(Lead).filter(Lead.user_id == campaign.user_id)
        
        if campaign.target_industry and campaign.target_industry != "All Industries":
            industries = [industry.strip() for industry in campaign.target_industry.split(",") if industry.strip()]
            if industries:
                query = query.filter(or_(*[Lead.industry.ilike(f"%{industry}%") for industry in industries]))
        
        matching_leads = query.all()
        print(f"Matching leads: {len(matching_leads)}")
        
        # Check for already sent leads
        sent_lead_ids = db.query(Email.lead_id).filter(Email.campaign_id == campaign.id).all()
        sent_count = len(sent_lead_ids)
        print(f"Already sent to: {sent_count} leads")
        
        # Check for unsent leads
        unsent_leads = [l for l in matching_leads if l.id not in [lid[0] for lid in sent_lead_ids]]
        print(f"Ready to send: {len(unsent_leads)} leads")
        
        if unsent_leads:
            print(f"Sample leads:")
            for lead in unsent_leads[:3]:
                print(f"  - {lead.first_name} {lead.last_name} ({lead.email}) | {lead.industry}")
        
        # Check daily limit status
        day_start_utc = local_now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
        day_end_utc = day_start_utc + timedelta(days=1)
        
        sent_today = db.query(Email).filter(
            Email.campaign_id == campaign.id,
            Email.sent_at.isnot(None),
            Email.sent_at >= day_start_utc,
            Email.sent_at < day_end_utc,
        ).count()
        
        daily_limit = max(campaign.daily_send_limit or 50, 1)
        remaining = max(daily_limit - sent_today, 0)
        
        print(f"Daily capacity: {sent_today}/{daily_limit} (remaining: {remaining})")
    
    # Check if there are ANY leads in the database
    print(f"\n{'─' * 80}")
    total_leads = db.query(Lead).count()
    print(f"Total leads in database: {total_leads}")
    
    if total_leads == 0:
        print("⚠️  WARNING: No leads found in database!")
    
    # Check if there are ANY campaigns
    all_campaigns = db.query(Campaign).all()
    print(f"Total campaigns: {len(all_campaigns)}")
    for c in all_campaigns:
        print(f"  - {c.name} ({c.status})")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

finally:
    db.close()
