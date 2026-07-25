"""add campaign whatsapp instance name

Revision ID: 20260527_wa_instance
Revises: 20260526_lead_user_email_unique
Create Date: 2026-05-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260527_wa_instance'
down_revision = '20260526_lead_user_email_unique'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('campaigns', sa.Column('evolution_instance_name', sa.String(), nullable=True))
    except Exception:
        pass


def downgrade():
    try:
        op.drop_column('campaigns', 'evolution_instance_name')
    except Exception:
        pass
