"""add support audit logs

Revision ID: 5e2b02e7bfda
Revises: a3f1c9d2e847
Create Date: 2026-06-05 23:08:00.000000

"""
from alembic import op
import sqlalchemy as sa
from core.database import GUID

# revision identifiers, used by Alembic.
revision = '5e2b02e7bfda'
down_revision = 'a3f1c9d2e847'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'support_audit_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('support_user_id', GUID(), nullable=False),
        sa.Column('impersonated_org_id', GUID(), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('flow_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['impersonated_org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['support_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('support_audit_logs')
