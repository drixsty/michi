"""add production performance indexes

Revision ID: 3e7a9c8f0d5a
Revises: 5e2b02e7bfda
Create Date: 2026-06-06 01:34:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3e7a9c8f0d5a'
down_revision = '5e2b02e7bfda'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Index sur user_id dans organization_members
    op.create_index('ix_organization_members_user_id', 'organization_members', ['user_id'], unique=False)
    
    # Indexes sur support_audit_logs
    op.create_index('ix_support_audit_logs_support_user_id', 'support_audit_logs', ['support_user_id'], unique=False)
    op.create_index('ix_support_audit_logs_impersonated_org_id', 'support_audit_logs', ['impersonated_org_id'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_support_audit_logs_impersonated_org_id', table_name='support_audit_logs')
    op.drop_index('ix_support_audit_logs_support_user_id', table_name='support_audit_logs')
    op.drop_index('ix_organization_members_user_id', table_name='organization_members')
