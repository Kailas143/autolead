import uuid

from sqlalchemy.orm import sessionmaker

from app import models
import app.workers.tasks as tasks


def test_create_lead_sets_user_id(client, db, test_user):
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": f"jane+{uuid.uuid4().hex}@example.com",
        "phone": "+1-555-0123",
        "company": "TestCorp",
        "title": "Marketing Lead",
        "industry": "SaaS"
    }

    response = client.post("/api/v1/leads/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["user_id"] == test_user.id

    lead = db.query(models.Lead).filter(models.Lead.id == data["id"]).first()
    assert lead is not None
    assert lead.user_id == test_user.id


def test_get_lead_returns_user_id(client, db, test_user):
    lead = models.Lead(
        first_name="Mike",
        last_name="Jones",
        email=f"mike+{uuid.uuid4().hex}@example.com",
        phone="+1-555-9876",
        user_id=test_user.id,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    response = client.get(f"/api/v1/leads/{lead.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == lead.id
    assert data["user_id"] == test_user.id


def test_csv_import_scopes_leads_to_user(client, db, test_user, monkeypatch):
    other_user = models.User(
        email=f"other+{uuid.uuid4().hex}@example.com",
        hashed_password="fake",
        is_active=True,
        is_superuser=False,
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    shared_email = f"shared+{uuid.uuid4().hex}@example.com"
    other_lead = models.Lead(
        first_name="Other",
        last_name="User",
        email=shared_email,
        user_id=other_user.id,
    )
    db.add(other_lead)
    db.commit()
    db.refresh(other_lead)

    # Force the task to use the same in-memory test database session factory.
    task_session = sessionmaker(autocommit=False, autoflush=False, bind=db.bind)
    monkeypatch.setattr(tasks, "SessionLocal", task_session)

    csv_content = "email,first_name,last_name,company\n" + \
        f"{shared_email},Jane,Doe,TestCorp\n"

    tasks.process_csv_import.run(test_user.id, csv_content, source="apollo")

    lead_for_test_user = db.query(models.Lead).filter(
        models.Lead.email == shared_email,
        models.Lead.user_id == test_user.id,
    ).first()

    assert lead_for_test_user is not None
    assert lead_for_test_user.id != other_lead.id
    assert lead_for_test_user.company == "TestCorp"
