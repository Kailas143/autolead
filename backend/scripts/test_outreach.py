import sys
import os
from sqlalchemy.orm import Session

# Add the parent directory to the path so we can import 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.lead import Lead
from app.models.campaign import Campaign, Sequence
from app.services.email_service import email_service
from app.services.ai_service import ai_service
from app.models.user import User

import asyncio

async def run_test_outreach():
    db = SessionLocal()
    try:
        # 1. Get or create a test user (owner of the campaign)
        user = db.query(User).filter(User.email == "demo@test.com").first()
        if not user:
            # For testing purposes, we'll try to find any user
            user = db.query(User).first()
            if not user:
                print("No users found in database. Create a user via the UI first.")
                return

        print(f"Using User: {user.email}")

        # 2. Create the Lead
        lead_email = "kailasvs94@gmail.com"
        lead = db.query(Lead).filter(Lead.email == lead_email).first()
        if not lead:
            lead = Lead(
                first_name="Kailas",
                last_name="VS",
                email=lead_email,
                company="Study Abroad Consultants",
                title="Owner",
                industry="Education Consulting",
                status="new"
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            print(f"Created Lead: {lead_email}")
        else:
            print(f"Lead already exists: {lead_email}")

        # 3. Create a Test Campaign
        campaign = db.query(Campaign).filter(Campaign.name == "Test Outreach Campaign").first()
        if not campaign:
            campaign = Campaign(
                name="Test Outreach Campaign",
                description="Verifying the end-to-end outreach flow",
                user_id=user.id
            )
            db.add(campaign)
            db.commit()
            db.refresh(campaign)
            print(f"Created Campaign: {campaign.name}")
        else:
            print(f"Campaign already exists: {campaign.name}")

        # 4. Create a Sequence Step
        sequence = db.query(Sequence).filter(Sequence.campaign_id == campaign.id).first()
        if not sequence:
            sequence = Sequence(
                campaign_id=campaign.id,
                step_number=1,
                subject="Question about {company}",
                body="Hi {first_name},\n\nI was looking at {company} and I think our AI systems could really help your study abroad consultancy scale.\n\n{personalization}\n\nBest,\nAurvyz Team",
                delay_days=0
            )
            db.add(sequence)
            db.commit()
            db.refresh(sequence)
            print(f"Created Sequence Step 1")
        else:
            print(f"Sequence already exists")

        # 5. Generate AI Personalization
        print("Generating AI personalization...")
        ai_line = await ai_service.generate_personalization({
            "first_name": lead.first_name,
            "company": lead.company,
            "title": lead.title,
            "industry": lead.industry
        })
        print(f"AI Line: {ai_line}")
        
        # Update lead with industry as placeholder for now
        lead.industry = ai_line
        db.commit()

        # 6. Send the Email
        print(f"Triggering email send to {lead_email}...")
        result = email_service.send_cold_email(db, campaign.id, lead.id, sequence.id)
        
        if result["status"] == "success":
            print(f"SUCCESS: Email sent! Resend ID: {result.get('resend_id')}")
        else:
            print(f"FAILED: {result.get('message')}")

    except Exception as e:
        print(f"ERROR during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_test_outreach())
