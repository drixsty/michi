"""Sprint 3 — Create cleaned_demand table

Revision ID: 002
Revises: 001
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cleaned_demand",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id",
            UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("raw_units_sold", sa.Float(), nullable=False),
        sa.Column("corrected_units_sold", sa.Float(), nullable=False),
        sa.Column("is_stockout", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_outlier", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("correction_type", sa.String(20), nullable=False, server_default="none"),
        sa.Column("computed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_cleaned_demand_product_id", "cleaned_demand", ["product_id"])
    op.create_index("ix_cleaned_demand_date", "cleaned_demand", ["date"])


def downgrade() -> None:
    op.drop_table("cleaned_demand")
