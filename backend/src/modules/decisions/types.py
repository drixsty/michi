import strawberry
from typing import List, Optional
from datetime import date

@strawberry.type
class FinancialKpiType:
    inventory_value_cost: float
    inventory_value_sale: float
    revenue_at_risk: float
    stock_coverage_avg_days: float
    currency: str
    is_mutualized: bool

@strawberry.type
class TopRiskType:
    product_id: strawberry.ID
    sku: str
    title: str
    risk_value: float
    stockout_date: Optional[date] = None
    reorder_quantity: int = 0
    days_of_stock: float = 0.0
    run_rate: float = 0.0
    supplier_id: Optional[strawberry.ID] = None
    source_platform: Optional[str] = None
    cost_price: float = 0.0
    sale_price: float = 0.0

@strawberry.type
class DecisionCenterOverviewType:
    kpis: FinancialKpiType
    top_risks: List[TopRiskType]
    total_run_rate: float = 0.0
    total_stock: int = 0
    health_score: int = 0
    message: Optional[str] = None
