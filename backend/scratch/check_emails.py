
from app.core.database import SessionLocal
from app.models.email import Email

db = SessionLocal()
try:
    emails = db.query(Email).order_by(Email.sent_at.desc()).limit(10).all()
    for e in emails:
        print(f"ID: {e.id}, Campaign: {e.campaign_id}, Lead: {e.lead_id}, Seq: {e.sequence_id}, Sent At: {e.sent_at}")
finally:
    db.close()
