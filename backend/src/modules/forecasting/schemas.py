"""
Pydantic Schemas — Forecasting
"""
from pydantic import BaseModel
from datetime import date, datetime
from uuid import UUID


class CleanedDemandSchema(BaseModel):
    id: UUID
    product_id: UUID
    date: date
    raw_units_sold: float
    corrected_units_sold: float
    is_stockout: bool
    is_outlier: bool
    correction_type: str
    computed_at: datetime

    model_config = {"from_attributes": True}


class PipelineResultSchema(BaseModel):
    success: bool
    products_processed: int
    rows_written: int
    stockout_corrections: int
    outlier_corrections: int
    message: str


class PredictionSchema(BaseModel):
    id: UUID
    product_id: UUID
    run_rate: float
    days_of_stock: float | None
    predicted_stockout_date: date | None
    reorder_quantity: int
    current_stock_snapshot: float
    lead_time_snapshot: int
    moq_snapshot: int
    computed_at: datetime

    model_config = {"from_attributes": True}


class PredictionRunResultSchema(BaseModel):
    success: bool
    products_processed: int
    message: str


class DashboardKPISchema(BaseModel):
    total_products: int
    actual_stockouts: int
    urgent_alerts: int
    predicted_stockouts_30d: int
    message: str
