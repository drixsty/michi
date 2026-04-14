"""003_sprint4_predictions

Revision ID: 003
Revises: 002
Create Date: 2025-04-06

US 2.8 — Création de la table predictions.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("run_rate", sa.Float, nullable=False),
        sa.Column("days_of_stock", sa.Float, nullable=True),
        sa.Column("predicted_stockout_date", sa.Date, nullable=True),
        sa.Column("reorder_quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("current_stock_snapshot", sa.Float, nullable=False),
        sa.Column("lead_time_snapshot", sa.Integer, nullable=False),
        sa.Column("moq_snapshot", sa.Integer, nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_predictions_product_id", "predictions", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_predictions_product_id", table_name="predictions")
    op.drop_table("predictions")
