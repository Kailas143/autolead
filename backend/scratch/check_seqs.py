
from app.core.database import SessionLocal
from app.models.campaign import Sequence

db = SessionLocal()
try:
    seqs = db.query(Sequence).filter(Sequence.campaign_id == 17).order_by(Sequence.step_number).all()
    for s in seqs:
        print(f"ID: {s.id}, Step: {s.step_number}, Delay: {s.delay_days}")
finally:
    db.close()
