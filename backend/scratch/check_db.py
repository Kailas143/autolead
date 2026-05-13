
from app.core.database import SessionLocal
from app.models.campaign import Campaign
from app.models.email import Email
from app.models.lead import Lead

db = SessionLocal()
try:
    campaigns = db.query(Campaign).all()
    print(f"Total Campaigns: {len(campaigns)}")
    for c in campaigns:
        email_count = db.query(Email).filter(Email.campaign_id == c.id).count()
        print(f"ID: {c.id}, Name: {c.name}, Status: {c.status}, Emails Sent: {email_count}")
        
    leads = db.query(Lead).all()
    print(f"Total Leads: {len(leads)}")
finally:
    db.close()
