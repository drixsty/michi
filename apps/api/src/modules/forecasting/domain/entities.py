"""
Domain Entities for Forecasting Module
Pure Python dataclasses (US 2.3 + US 2.8)
"""
from dataclasses import dataclass
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
    inventory_level: Optional[int]
    is_stockout: bool
    is_outlier: bool
    correction_type: str  # "none" | "stockout" | "outlier" | "stockout+outlier"
    computed_at: datetime

@dataclass
class PredictionEntity:
    id: UUID
    product_id: UUID
    run_rate: float
    days_of_stock: Optional[float]
    predicted_stockout_date: Optional[date]
    reorder_quantity: int
    current_stock_snapshot: float
    lead_time_snapshot: int
    moq_snapshot: int
    mape_score: Optional[float]
    abc_rank: Optional[str]
    annual_gross_profit: Optional[float]
    computed_at: datetime
