from unittest.mock import patch
import uuid

from app import models
from app.models.communication import Communication


def create_lead(db, user):
    lead = models.Lead(
        first_name="John",
        last_name="Doe",
        email=f"john+{uuid.uuid4().hex}@example.com",
        phone="+1 (555) 123-4567",
        user_id=user.id,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def create_whatsapp_campaign(db, user):
    campaign = models.Campaign(
        name="WhatsApp Campaign",
        channel="whatsapp",
        user_id=user.id,
    )
    db.add(campaign)
    db.flush()

    sequence = models.Sequence(
        campaign_id=campaign.id,
        step_number=1,
        subject="Hello",
        body="Hi {first_name}, welcome!",
        delay_days=0,
    )
    db.add(sequence)
    db.commit()
    db.refresh(campaign)
    db.refresh(sequence)
    return campaign, sequence


def test_manual_whatsapp_send_creates_communication(client, db, test_user):
    lead = create_lead(db, test_user)

    with patch(
        "app.api.v1.endpoints.leads.whatsapp_service.create_instance_sync",
        return_value={"instance": "ok"},
    ) as mock_create, patch(
        "app.api.v1.endpoints.leads.whatsapp_service.send_message_sync",
        return_value=True,
    ) as mock_send:
        response = client.post(
            f"/api/v1/leads/{lead.id}/whatsapp",
            json={"message": "Hello John"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_create.assert_called_once()
    mock_send.assert_called_once()

    communication = (
        db.query(Communication)
        .filter(Communication.lead_id == lead.id, Communication.channel == "whatsapp")
        .first()
    )
    assert communication is not None
    assert communication.body == "Hello John"
    assert communication.subject == "Manual WhatsApp Message"


def test_campaign_whatsapp_send_creates_communication(client, db, test_user):
    lead = create_lead(db, test_user)
    campaign, sequence = create_whatsapp_campaign(db, test_user)

    with patch(
        "app.api.v1.endpoints.campaigns.whatsapp_service.create_instance_sync",
        return_value={"instance": "ok"},
    ) as mock_create, patch(
        "app.api.v1.endpoints.campaigns.whatsapp_service.send_message_sync",
        return_value=True,
    ) as mock_send:
        response = client.post(
            f"/api/v1/campaigns/{campaign.id}/send-lead/{lead.id}",
            json={"sequence_id": sequence.id},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_create.assert_called_once()
    mock_send.assert_called_once()

    communication = (
        db.query(Communication)
        .filter(Communication.lead_id == lead.id, Communication.campaign_id == campaign.id)
        .first()
    )
    assert communication is not None
    assert communication.body == f"Hi {lead.first_name}, welcome!"
    assert communication.channel == "whatsapp"
