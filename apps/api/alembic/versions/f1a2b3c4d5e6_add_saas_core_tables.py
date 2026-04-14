"""add_saas_core_tables

Revision ID: f1a2b3c4d5e6
Revises: 001
Branch Labels: None
Depends on: None

Creates the SaaS multi-tenant core tables: users, organizations,
organization_members, stores.

NOTE: Uses IF NOT EXISTS throughout so this migration is idempotent — safe
to run even if seed_v2.py already created the tables via
Base.metadata.create_all.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # ENUM types  (idempotent — DO block swallows duplicate_object)
    # ------------------------------------------------------------------
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('admin', 'manager', 'viewer');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE invitationstatus AS ENUM ('pending', 'accepted', 'expired');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE platformsource AS ENUM
                ('SHOPIFY', 'WOOCOMMERCE', 'AMAZON', 'CSV', 'CUSTOM');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    # ------------------------------------------------------------------
    # organizations
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id          UUID        NOT NULL DEFAULT gen_random_uuid(),
            name        VARCHAR(255) NOT NULL,
            slug        VARCHAR(255) NOT NULL,
            stripe_customer_id VARCHAR(255),
            plan        VARCHAR(50)  NOT NULL DEFAULT 'BASIC',
            subscription_status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
            created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id)
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_organizations_slug
            ON organizations (slug);
    """)

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id                      UUID        NOT NULL DEFAULT gen_random_uuid(),
            email                   VARCHAR(255) NOT NULL,
            hashed_password         VARCHAR(255),
            google_id               VARCHAR(255),
            shop_id                 UUID,
            current_organization_id UUID,
            created_at              TIMESTAMP   NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMP   NOT NULL DEFAULT NOW(),
            preferences             JSONB       NOT NULL DEFAULT '{}',
            PRIMARY KEY (id)
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email    ON users (email);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id) WHERE google_id IS NOT NULL;")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_shop_id ON users (shop_id);")

    # ------------------------------------------------------------------
    # organization_members
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS organization_members (
            organization_id UUID NOT NULL,
            user_id         UUID NOT NULL,
            role            userrole NOT NULL DEFAULT 'viewer',
            permissions     JSONB    NOT NULL DEFAULT '{}',
            joined_at       TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (organization_id, user_id),
            FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id)         REFERENCES users         (id) ON DELETE CASCADE
        );
    """)

    # ------------------------------------------------------------------
    # stores
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id              UUID        NOT NULL DEFAULT gen_random_uuid(),
            organization_id UUID        NOT NULL,
            name            VARCHAR(255) NOT NULL,
            platform        platformsource NOT NULL,
            connected       BOOLEAN     NOT NULL DEFAULT FALSE,
            last_sync_at    TIMESTAMP,
            health_status   VARCHAR(50)  DEFAULT 'HEALTHY',
            config          JSONB        NOT NULL DEFAULT '{}',
            created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id),
            FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE CASCADE
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_stores_organization_id ON stores (organization_id);")
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uix_org_platform
            ON stores (organization_id, platform);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS stores CASCADE;")
    op.execute("DROP TABLE IF EXISTS organization_members CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
    op.execute("DROP TABLE IF EXISTS organizations CASCADE;")
    op.execute("DROP TYPE IF EXISTS platformsource;")
    op.execute("DROP TYPE IF EXISTS invitationstatus;")
    op.execute("DROP TYPE IF EXISTS userrole;")
