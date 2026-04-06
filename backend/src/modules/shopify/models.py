"""
SQLAlchemy Models — Shopify (Products & SalesLogs)
"""
from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    sku = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    lead_time = Column(Integer, nullable=False, default=14)   # jours
    moq = Column(Integer, nullable=False, default=10)         # minimum order quantity

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    sales_logs = relationship("SalesLog", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.sku} — {self.title}>"


class SalesLog(Base):
    __tablename__ = "sales_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)
    units_sold = Column(Float, nullable=False, default=0.0)
    end_of_day_stock = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="sales_logs")

    def __repr__(self):
        return f"<SalesLog product={self.product_id} date={self.date} sold={self.units_sold}>"
