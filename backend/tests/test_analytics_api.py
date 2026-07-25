import uuid
from datetime import datetime, timezone, timedelta

from app.models.communication import Communication
from app import models


def setup_campaign_and_sequence(db, user):
    campaign = models.Campaign(name="Test Campaign", channel="email", user_id=user.id)
    db.add(campaign)
    db.flush()
    seq = models.Sequence(campaign_id=campaign.id, step_number=1, subject="S", body="B", delay_days=0)
    db.add(seq)
    db.commit()
    db.refresh(campaign)
    db.refresh(seq)
    return campaign, seq


def create_comm(db, lead, campaign=None, sequence=None, subject="Hello", body="Hi", sent_at=None, opened=False, replied=False, channel="email"):
    comm = Communication(
        lead_id=lead.id,
        campaign_id=campaign.id if campaign else None,
        sequence_id=sequence.id if sequence else None,
        channel=channel,
        provider="test",
        provider_id=str(uuid.uuid4()),
        subject=subject,
        body=body,
        status="sent",
        sent_at=sent_at or datetime.now(timezone.utc),
        opened=opened,
        replied=replied,
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return comm


def test_analytics_stats_and_outreach_log(client, db, test_user):
    # Create lead and campaign
    lead = models.Lead(first_name="A", last_name="B", email=f"lead+{uuid.uuid4().hex}@example.com", user_id=test_user.id)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    campaign, seq = setup_campaign_and_sequence(db, test_user)

    # Create communications
    now = datetime.now(timezone.utc)
    create_comm(db, lead, campaign=campaign, sequence=seq, sent_at=now - timedelta(days=1), opened=True)
    create_comm(db, lead, campaign=campaign, sequence=seq, sent_at=now, replied=True)

    resp = client.get('/api/v1/analytics/stats')
    assert resp.status_code == 200
    data = resp.json()

    assert data['summary']['total_leads'] >= 1
    assert data['summary']['total_messages_sent'] >= 2
    assert 'open_rate' in data['summary']
    assert 'reply_rate' in data['summary']

    # Outreach log
    resp2 = client.get('/api/v1/analytics/outreach-log')
    assert resp2.status_code == 200
    logs = resp2.json()
    assert any(l['id'] == lead.id and l['messages_sent'] >= 2 for l in logs)


def test_sent_messages_listing(client, db, test_user):
    lead = models.Lead(first_name="C", last_name="D", email=f"lead+{uuid.uuid4().hex}@example.com", user_id=test_user.id)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    campaign = models.Campaign(name="Camp 2", channel="email", user_id=test_user.id)
    db.add(campaign)
    db.flush()
    seq = models.Sequence(campaign_id=campaign.id, step_number=1, subject="Sub", body="Body", delay_days=0)
    db.add(seq)
    db.commit()
    db.refresh(campaign)

    create_comm(db, lead, campaign=campaign, sequence=seq, subject="S1", body="B1", sent_at=datetime.now(timezone.utc))

    resp = client.get('/api/v1/analytics/sent-messages')
    assert resp.status_code == 200
    payload = resp.json()
    assert 'messages' in payload
    assert any(m['customer_email'] == lead.email for m in payload['messages'])
