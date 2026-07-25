from app.core.database import SessionLocal
from app.models.lead import Lead

db = SessionLocal()
lead = db.query(Lead).order_by(Lead.id.desc()).first()
print(f"Lead {lead.id}: phone={lead.phone}, status={lead.status}, whatsapp_status={lead.whatsapp_status}")
