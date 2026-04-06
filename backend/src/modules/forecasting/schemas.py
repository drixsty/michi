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
