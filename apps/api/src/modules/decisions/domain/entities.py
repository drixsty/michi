"""
Domain Entities — Decisions Module
Pure Python dataclasses to isolate business logic from infrastructure.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from uuid import UUID

@dataclass(frozen=True)
class FinancialKpis:
    inventory_value_cost: float
    inventory_value_sale: float
    revenue_at_risk: float
    stock_coverage_avg_days: float
    currency: str = "€"
    is_mutualized: bool = False

@dataclass(frozen=True)
class RiskItem:
    product_id: UUID
    sku: str
    title: str
    risk_value: float
    stockout_date: Optional[str]
    reorder_quantity: int
    days_of_stock: float
    run_rate: float
    supplier_id: Optional[str]
    source_platform: str
    cost_price: float
    sale_price: float

@dataclass(frozen=True)
class DecisionCenterOverview:
    kpis: FinancialKpis
    top_risks: List[RiskItem]
    total_run_rate: float
    total_stock: int
    health_score: int
    active_platforms: List[str]
    capital_breakdown: List[Dict[str, Any]]
    message: str
