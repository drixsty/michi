"""add_reorder_alert_date

Revision ID: a3f1c9d2e847
Revises: e49c6b8e7bfc
Create Date: 2026-05-26 00:00:00.000000

Ajout de reorder_alert_date sur la table predictions.
Correspond au Reorder Point (ROP) date : date limite à laquelle passer la commande
pour recevoir le stock avant la date de rupture prévisionnelle.

Formule : reorder_alert_date = predicted_stockout_date - effective_lead_time
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a3f1c9d2e847'
down_revision: Union[str, None] = 'e68ec673a334'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('predictions', sa.Column('reorder_alert_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('predictions', 'reorder_alert_date')
