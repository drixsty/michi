"""
SQLAlchemy Models — Forecasting (US 2.3 + US 2.8)

CleanedDemand : demande corrigée après pipeline OOS + IQR.
Prediction     : run rate + prédiction de rupture + recommandation de commande.
"""
from sqlalchemy import Column, Date, Float, Boolean, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.core.database import Base
from src.modules.inventory.models import Product  # Import requis pour les relations


class CleanedDemand(Base):
    __tablename__ = "cleaned_demand"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date = Column(Date, nullable=False, index=True)
    raw_units_sold = Column(Float, nullable=False)        # valeur brute (sales_log)
    corrected_units_sold = Column(Float, nullable=False)  # valeur finale après pipeline

    is_stockout = Column(Boolean, nullable=False, default=False)
    is_outlier = Column(Boolean, nullable=False, default=False)

    # "none" | "stockout" | "outlier" | "stockout+outlier"
    correction_type = Column(String(20), nullable=False, default="none")

    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="cleaned_demands")

    def __repr__(self):
        return (
            f"<CleanedDemand product={self.product_id} "
            f"date={self.date} corrected={self.corrected_units_sold:.2f}>"
        )


class Prediction(Base):
    """
    Prédiction opérationnelle par produit (US 2.8).

    Une ligne par produit par run — contient le run rate calculé,
    la date prévisionnelle de rupture et la quantité de commande recommandée.
    """
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Run rate (US 2.5) — unités/jour sur les 30 derniers jours nettoyés
    run_rate = Column(Float, nullable=False)

    # Nombre de jours de stock restants au moment du calcul
    days_of_stock = Column(Float, nullable=True)

    # Date prévisionnelle de rupture (None si run_rate == 0)
    predicted_stockout_date = Column(Date, nullable=True)

    # Quantité de commande recommandée (US 2.7), multiple du MOQ
    reorder_quantity = Column(Integer, nullable=False, default=0)

    # Snapshot des paramètres produit au moment du calcul
    current_stock_snapshot = Column(Float, nullable=False)
    lead_time_snapshot = Column(Integer, nullable=False)
    moq_snapshot = Column(Integer, nullable=False)

    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="prediction")

    def __repr__(self):
        return (
            f"<Prediction product={self.product_id} "
            f"run_rate={self.run_rate:.2f} "
            f"stockout={self.predicted_stockout_date}>"
        )
