"""
SQLAlchemy Models — Inventory (Unified Product & Sales History)
This is the core source of truth for all Michi modules (Forecasting, Alerts, etc.).
It decouples the store platform (Shopify, Amazon, Woo) from our business logic.
"""
from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey, DateTime, Enum, Boolean, UniqueConstraint, Uuid, JSON
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
import uuid

from database import Base, GUID

from src.modules.inventory.domain.entities import PlatformSource

class Store(Base):
    """
    Store Model: Represents a connected store (Shopify, Amazon, etc.)
    belonging to an Organization.
    """
    __tablename__ = "stores"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    platform = Column(Enum(PlatformSource), nullable=False)
    connected = Column(Boolean, default=False, nullable=False)
    
    # Discovery & Sync Status
    last_sync_at = Column(DateTime, nullable=True)
    health_status = Column(String(50), default="HEALTHY") # HEALTHY, ERROR, UNKNOWN
    
    # Store-specific credentials/config (Sprint 15+)
    config = Column(JSON, default={}, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('organization_id', 'platform', name='uix_org_platform'),
    )

    # Relationships
    organization = relationship("Organization", back_populates="stores")
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="store", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="store", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Store {self.name} ({self.platform.value})>"

class Product(Base):
    __tablename__ = "products"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    store_id = Column(GUID, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)

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
    external_id = Column(String(255), nullable=True) # ID in the source platform

    # Supplier link
    supplier_id = Column(GUID, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    store = relationship("Store", back_populates="products")
    sales_logs = relationship("SalesLog", back_populates="product", cascade="all, delete-orphan")
    prediction = relationship("Prediction", back_populates="product", uselist=False, cascade="all, delete-orphan")
    cleaned_demands = relationship("CleanedDemand", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")
    supplier = relationship("Supplier", back_populates="products")

    def __repr__(self):
        return f"<Product {self.sku} — {self.title}>"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    type = Column(String(50), nullable=False) 
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    severity = Column(Integer, default=1) 
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="alerts")

class SalesLog(Base):
    __tablename__ = "sales_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)
    units_sold = Column(Float, nullable=False, default=0.0)
    end_of_day_stock = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="sales_logs")

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    store_id = Column(GUID, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)

    # Performance metrics
    reliability_score = Column(Float, default=1.0)
    average_delay_days = Column(Float, default=0.0)

    store = relationship("Store", back_populates="suppliers")
    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

class AlertEmail(Base):
    __tablename__ = "alert_emails"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String(50), default="stockout_imminent")

    product = relationship("Product")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    store_id = Column(GUID, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(GUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(GUID, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)

    quantity = Column(Integer, nullable=False)
    order_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    expected_arrival_date = Column(Date, nullable=False)
    actual_arrival_date = Column(Date, nullable=True)

    status = Column(String(50), default="PENDING")

    store = relationship("Store", back_populates="purchase_orders")
    supplier = relationship("Supplier", back_populates="purchase_orders")
