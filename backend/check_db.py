from app.core.database import SessionLocal
from app.models.communication import Communication

db = SessionLocal()
comms = db.query(Communication).filter(Communication.channel == "whatsapp").order_by(Communication.id.desc()).limit(5).all()
for c in comms:
    print(f"[{c.sent_at}] Lead {c.lead_id}: {c.status}")
db.close()
