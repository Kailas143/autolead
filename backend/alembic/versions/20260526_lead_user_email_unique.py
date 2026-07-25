"""make lead email unique per user

Revision ID: 20260526_lead_user_email_unique
Revises: 20260525_communications_unified
Create Date: 2026-05-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260526_lead_user_email_unique'
down_revision = '20260525_communications_unified'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        # Common Postgres unique constraint names for single-column unique=True
        for constraint_name in ['leads_email_key', 'uq_leads_email', 'email']:  # try common names
            try:
                op.drop_constraint(constraint_name, 'leads', type_='unique')
            except Exception:
                pass
    else:
        try:
            op.drop_index('ix_leads_email', table_name='leads')
        except Exception:
            pass

    try:
        op.create_unique_constraint('uq_leads_user_email', 'leads', ['user_id', 'email'])
    except Exception:
        # In case the existing table already has the constraint or index, ignore failures.
        pass


def downgrade():
    try:
        op.drop_constraint('uq_leads_user_email', 'leads', type_='unique')
    except Exception:
        pass

    try:
        op.create_unique_constraint('uq_leads_email', 'leads', ['email'])
    except Exception:
        pass
