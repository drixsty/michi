"""Sprint 1 — Create products and sales_logs tables

Revision ID: 001
Revises:
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("shop_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("current_stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lead_time", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("moq", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_products_shop_id", "products", ["shop_id"])

    op.create_table(
        "sales_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id",
            UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("units_sold", sa.Float(), nullable=False, server_default="0"),
        sa.Column("end_of_day_stock", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_sales_logs_product_id", "sales_logs", ["product_id"])
    op.create_index("ix_sales_logs_date", "sales_logs", ["date"])


def downgrade() -> None:
    op.drop_table("sales_logs")
    op.drop_table("products")
