from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

class IngestedProduct(BaseModel):
    """Format normalisé pour un produit importé."""
    sku: str
    title: str
    description: Optional[str] = None
    barcode: Optional[str] = None
    price: float = 0.0
    current_stock: int = 0
    category: Optional[str] = None
    image_url: Optional[str] = None
    vendor: Optional[str] = None

class IngestedSale(BaseModel):
    """Format normalisé pour une vente importée."""
    sku: str
    date: date
    units_sold: int
    stock_at_end: Optional[int] = None
    order_id: Optional[str] = None

class IngestionResult(BaseModel):
    """Résultat global d'une opération d'ingestion."""
    store_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    products_count: int
    sales_count: int
    errors: List[str] = []
