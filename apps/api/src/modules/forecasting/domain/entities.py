"""
Domain Entities for Forecasting Module
Pure Python dataclasses (US 2.3 + US 2.8)
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID

@dataclass
class CleanedDemandEntity:
    id: UUID
    product_id: UUID
    date: date
    raw_units_sold: float
    corrected_units_sold: float
    inventory_level: Optional[int] = None
    is_stockout: bool = False
    is_outlier: bool = False
    correction_type: str = "none"  # "none" | "stockout" | "outlier" | "stockout+outlier"
    computed_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PredictionEntity:
    id: UUID
    product_id: UUID
    run_rate: float
    days_of_stock: Optional[float] = None
    predicted_stockout_date: Optional[date] = None
    reorder_quantity: int = 0
    current_stock_snapshot: float = 0.0
    lead_time_snapshot: int = 14
    moq_snapshot: int = 1
    mape_score: Optional[float] = None
    abc_rank: Optional[str] = None
    annual_gross_profit: Optional[float] = None
    computed_at: datetime = field(default_factory=datetime.utcnow)
