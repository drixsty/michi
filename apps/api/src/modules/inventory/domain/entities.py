from core.database.models import Organization, User, OrganizationMember
"""
Domain Entities — Inventory Module
Pure Python dataclasses to isolate business logic from infrastructure (SQLAlchemy).
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from enum import Enum

class PlatformSource(Enum):
    SHOPIFY = "SHOPIFY"
    WOOCOMMERCE = "WOOCOMMERCE"
    AMAZON = "AMAZON"
    CSV = "CSV"
    CUSTOM = "CUSTOM"

@dataclass
class StoreEntity:
    id: UUID
    organization_id: UUID
    name: str
    platform: PlatformSource
    connected: bool = False
    last_sync_at: Optional[datetime] = None
    health_status: str = "HEALTHY"
    config: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ProductEntity:
    id: UUID
    store_id: UUID
    sku: str
    title: str
    current_stock: int = 0
    lead_time: int = 14
    moq: int = 10
    boost_factor: float = 1.0
    stock_weight: float = 1.0
    cost_price: Optional[float] = None
    sale_price: Optional[float] = None
    source_platform: PlatformSource = PlatformSource.CUSTOM
    external_id: Optional[str] = None
    supplier_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SalesLogEntity:
    id: UUID
    product_id: UUID
    date: date
    units_sold: float = 0.0
    end_of_day_stock: int = 0

@dataclass
class AlertEntity:
    id: UUID
    product_id: UUID
    type: str
    message: str
    is_read: bool = False
    severity: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SupplierEntity:
    id: UUID
    store_id: UUID
    name: str
    contact_email: Optional[str] = None
    reliability_score: float = 1.0
    average_delay_days: float = 0.0
    lead_time_sigma: float = 0.0

@dataclass
class PurchaseOrderEntity:
    id: UUID
    store_id: UUID
    product_id: UUID
    supplier_id: UUID
    quantity: int
    order_date: date
    expected_arrival_date: date
    actual_arrival_date: Optional[date] = None
    status: str = "PENDING"
