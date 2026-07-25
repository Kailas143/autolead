"""add sequence delay minutes

Revision ID: 20260527_seq_delay_min
Revises: 20260527_wa_instance
Create Date: 2026-05-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260527_seq_delay_min'
down_revision = '20260527_wa_instance'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('sequences', sa.Column('delay_minutes', sa.Integer(), nullable=True, server_default='0'))
    except Exception:
        pass

    try:
        op.alter_column('sequences', 'delay_minutes', server_default=None)
    except Exception:
        pass


def downgrade():
    try:
        op.drop_column('sequences', 'delay_minutes')
    except Exception:
        pass
