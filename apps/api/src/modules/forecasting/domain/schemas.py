"""
Forecasting Schemas — Pydantic DTOs for the Application Layer.
"""
from pydantic import BaseModel

class PipelineResultSchema(BaseModel):
    success: bool
    products_processed: int
    rows_written: int
    stockout_corrections: int
    outlier_corrections: int
    message: str

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
