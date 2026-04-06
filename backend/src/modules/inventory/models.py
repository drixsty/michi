"""
SQLAlchemy Models — Inventory (Unified Product & Sales History)
This is the core source of truth for all Michi modules (Forecasting, Alerts, etc.).
It decouples the store platform (Shopify, Amazon, Woo) from our business logic.
"""
from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
import uuid

from src.core.database import Base

class PlatformSource(enum.Enum):
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    AMAZON = "amazon"
    CSV = "csv"
    CUSTOM = "custom"

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Agnostic core data
    sku = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    
    # Supply chain parameters
    lead_time = Column(Integer, nullable=False, default=14)   # days
    moq = Column(Integer, nullable=False, default=10)         # minimum order quantity

    # Traceability
    source_platform = Column(Enum(PlatformSource), nullable=False, default=PlatformSource.CUSTOM)
    external_id = Column(String(255), nullable=True) # ID in the source platform (Shopify Product ID, etc.)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    sales_logs = relationship("SalesLog", back_populates="product", cascade="all, delete-orphan")
    prediction = relationship("Prediction", back_populates="product", uselist=False, cascade="all, delete-orphan")
    cleaned_demands = relationship("CleanedDemand", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.sku} ({self.source_platform.value}) — {self.title}>"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    type = Column(String(50), nullable=False) # e.g., "STOCKOUT_RISK", "CRITICAL_STOCK"
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    severity = Column(Integer, default=1) # 1: Low, 2: Med, 3: High
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="alerts")

    def __repr__(self):
        return f"<Alert type={self.type} product={self.product_id} is_read={self.is_read}>"


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
