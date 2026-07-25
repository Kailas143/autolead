"""add lead whatsapp status

Revision ID: 20260527_lead_wa_stat
Revises: 20260527_seq_delay_min
Create Date: 2026-05-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260527_lead_wa_stat'
down_revision = '20260527_seq_delay_min'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('leads', sa.Column('whatsapp_status', sa.String(), nullable=True, server_default='unknown'))
    except Exception:
        pass

    try:
        op.execute("UPDATE leads SET whatsapp_status = 'missing' WHERE phone IS NULL OR TRIM(phone) = ''")
    except Exception:
        pass

    try:
        op.alter_column('leads', 'whatsapp_status', nullable=False, server_default=None)
    except Exception:
        pass


def downgrade():
    try:
        op.drop_column('leads', 'whatsapp_status')
    except Exception:
        pass
