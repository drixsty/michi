"""
SQLAlchemy Models — Forecasting (US 2.3 + US 2.8)

CleanedDemand: Corrected demand after OOS + IQR pipeline.
Prediction: Run rate + stockout prediction + order recommendation.
"""
from sqlalchemy import Column, Date, Float, Boolean, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from core.database import Base, GUID
from modules.inventory.infrastructure.persistence.models import Product  # Import requis pour les relations


class CleanedDemand(Base):
    __tablename__ = "cleaned_demand"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(
        GUID,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date = Column(Date, nullable=False, index=True)
    raw_units_sold = Column(Float, nullable=False)        # valeur brute (sales_log)
    corrected_units_sold = Column(Float, nullable=False)  # valeur finale après pipeline
    inventory_level = Column(Integer, nullable=True)     # stock fin de journée

    is_stockout = Column(Boolean, nullable=False, default=False)
    is_outlier = Column(Boolean, nullable=False, default=False)

    # "none" | "stockout" | "outlier" | "stockout+outlier"
    correction_type = Column(String(20), nullable=False, default="none")

    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

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

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(
        GUID,
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
    moq_snapshot = Column(Integer, nullable=False, default=1)
    
    # Précision de l'IA (Sprint 10) — Mean Absolute Percentage Error
    # Exprimé en % (ex: 15.5 pour 15.5% d'erreur)
    mape_score = Column(Float, nullable=True)

    # --- Sprint 15 : Analyse ABC par la marge ---
    abc_rank = Column(String(10), nullable=True) # "A", "B", "C"
    annual_gross_profit = Column(Float, nullable=True) # Profit annuel estimé
    demand_sigma = Column(Float, nullable=True, default=0.0) # Écart-type de la demande (DS v2)

    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    product = relationship("Product", back_populates="prediction")

    def __repr__(self):
        return (
            f"<Prediction product={self.product_id} "
            f"run_rate={self.run_rate:.2f} "
            f"stockout={self.predicted_stockout_date}>"
        )
