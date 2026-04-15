"""
Pydantic Schemas — Shopify
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import UUID


class ProductSchema(BaseModel):
    id: UUID
    shop_id: UUID
    sku: str
    title: str
    current_stock: int
    lead_time: int
    moq: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SalesLogSchema(BaseModel):
    id: UUID
    product_id: UUID
    date: date
    units_sold: float
    end_of_day_stock: int

    model_config = {"from_attributes": True}


class SyncResultSchema(BaseModel):
    success: bool
    products_created: int
    sales_logs_created: int
    message: str


class ValidationIssue(BaseModel):
    rule: str
    severity: str   # "error" | "warning"
    detail: str


class ValidationReportSchema(BaseModel):
    is_valid: bool
    product_count: int
    sales_log_count: int
    stockout_ratio: float       # ex: 0.12 → 12%
    issues: list[ValidationIssue]
    summary: str
