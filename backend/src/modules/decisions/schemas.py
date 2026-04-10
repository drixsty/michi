from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class FinancialKpiSchema(BaseModel):
    inventory_value_cost: float
    inventory_value_sale: float
    revenue_at_risk: float
    stock_coverage_avg_days: float
    currency: str
    is_mutualized: bool

class DecisionCenterOverview(BaseModel):
    kpis: FinancialKpiSchema
    top_risks: List[dict]
    total_run_rate: float = 0.0
    total_stock: int = 0
    health_score: int = 0
    message: Optional[str] = None
