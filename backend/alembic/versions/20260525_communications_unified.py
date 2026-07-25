"""add communications indexes and notes

Revision ID: 20260525_communications_unified
Revises: 
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260525_communications_unified'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Ensure communications table exists and add helpful indexes for analytics
    op.create_index('ix_communications_provider_id', 'communications', ['provider_id'], unique=False)
    op.create_index('ix_communications_campaign_id', 'communications', ['campaign_id'], unique=False)
    op.create_index('ix_communications_lead_id', 'communications', ['lead_id'], unique=False)
    try:
        op.create_index('ix_communications_sent_at', 'communications', ['sent_at'], unique=False)
    except Exception:
        pass


def downgrade():
    op.drop_index('ix_communications_provider_id', table_name='communications')
    op.drop_index('ix_communications_campaign_id', table_name='communications')
    op.drop_index('ix_communications_lead_id', table_name='communications')
    try:
        op.drop_index('ix_communications_sent_at', table_name='communications')
    except Exception:
        pass
