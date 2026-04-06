"""
SQLAlchemy Model — CleanedDemand (US 2.3)
Stocke la demande corrigée après passage dans la pipeline OOS + IQR.
"""
from sqlalchemy import Column, Date, Float, Boolean, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.core.database import Base


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

    def __repr__(self):
        return (
            f"<CleanedDemand product={self.product_id} "
            f"date={self.date} corrected={self.corrected_units_sold:.2f}>"
        )
