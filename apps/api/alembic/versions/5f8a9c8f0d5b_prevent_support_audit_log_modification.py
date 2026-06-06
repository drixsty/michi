"""prevent support_audit_log modification

Revision ID: 5f8a9c8f0d5b
Revises: 3e7a9c8f0d5a
Create Date: 2026-06-06 02:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5f8a9c8f0d5b'
down_revision = '3e7a9c8f0d5a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'postgresql':
        # Crée la fonction trigger pour Postgres
        op.execute("""
            CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'Updates or deletes are not allowed on support_audit_logs table';
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Crée le trigger pour Postgres
        op.execute("""
            CREATE TRIGGER check_audit_log_modification
            BEFORE UPDATE OR DELETE ON support_audit_logs
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_log_modification();
        """)
    elif dialect == 'sqlite':
        # Crée les triggers SQLite
        op.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_update_audit_logs
            BEFORE UPDATE ON support_audit_logs
            BEGIN
                SELECT RAISE(FAIL, 'Updates not allowed on support_audit_logs');
            END;
        """)
        op.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_delete_audit_logs
            BEFORE DELETE ON support_audit_logs
            BEGIN
                SELECT RAISE(FAIL, 'Deletes not allowed on support_audit_logs');
            END;
        """)


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'postgresql':
        op.execute("DROP TRIGGER IF EXISTS check_audit_log_modification ON support_audit_logs;")
        op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_modification();")
    elif dialect == 'sqlite':
        op.execute("DROP TRIGGER IF EXISTS prevent_update_audit_logs;")
        op.execute("DROP TRIGGER IF EXISTS prevent_delete_audit_logs;")
