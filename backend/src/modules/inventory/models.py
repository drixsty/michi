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
    
    # Algorithmic Parameters (Sprint 12)
    boost_factor = Column(Float, nullable=False, default=1.0) # seasonality multiplier
    stock_weight = Column(Float, nullable=False, default=1.0) # channel priority weighting

    # Financial Data (Sprint 13)
    cost_price = Column(Float, nullable=True) # purchase cost unit
    sale_price = Column(Float, nullable=True) # selling price unit

    # Traceability
    source_platform = Column(Enum(PlatformSource), nullable=False, default=PlatformSource.CUSTOM)
    external_id = Column(String(255), nullable=True) # ID in the source platform (Shopify Product ID, etc.)

    # Supplier link (Sprint 8)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    sales_logs = relationship("SalesLog", back_populates="product", cascade="all, delete-orphan")
    prediction = relationship("Prediction", back_populates="product", uselist=False, cascade="all, delete-orphan")
    cleaned_demands = relationship("CleanedDemand", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")
    supplier = relationship("Supplier", back_populates="products")

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


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)

    # Performance metrics
    reliability_score = Column(Float, default=1.0) # 1.0 = 100% on-time
    average_delay_days = Column(Float, default=0.0) # avg days late

    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier {self.name} reliability={self.reliability_score:.2%}>"


class AlertEmail(Base):
    """
    Suivi des alertes email envoyées pour éviter le spam (US 10.4).
    """
    __tablename__ = "alert_emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String(50), default="stockout_imminent")

    product = relationship("Product")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)

    quantity = Column(Integer, nullable=False)
    order_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    expected_arrival_date = Column(Date, nullable=False)
    actual_arrival_date = Column(Date, nullable=True)

    # PENDING, RECEIVED, CANCELLED
    status = Column(String(50), default="PENDING")

    supplier = relationship("Supplier", back_populates="purchase_orders")

class SourceConnection(Base):
    """
    Persistance de la connexion à une plateforme source (US Sprint 17).
    Stocke si la source est active, quand elle a été sync pour la dernière fois 
    et son état de santé (API metrics).
    """
    __tablename__ = "source_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    platform = Column(Enum(PlatformSource), nullable=False)
    connected = Column(Boolean, default=False, nullable=False)
    
    last_sync_at = Column(DateTime, nullable=True)
    health_status = Column(String(50), default="HEALTHY") # HEALTHY, ERROR, UNKNOWN

    def __repr__(self):
        return f"<SourceConnection {self.platform.value} connected={self.connected}>"
