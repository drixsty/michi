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

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def __contains__(self, item):
        return hasattr(self, item)

    def get(self, item, default=None):
        return getattr(self, item, default)

class IngestedSale(BaseModel):
    """Format normalisé pour une vente importée."""
    sku: str
    date: date
    units_sold: int
    stock_at_end: Optional[int] = None
    end_of_day_stock: Optional[int] = None
    order_id: Optional[str] = None
    is_anomaly: Optional[bool] = None
    is_interpolated: Optional[bool] = None

    def __getitem__(self, item):
        try:
            # Dual support for both names
            if item == "end_of_day_stock":
                return self.end_of_day_stock if self.end_of_day_stock is not None else (self.stock_at_end or 0)
            if item == "stock_at_end":
                return self.stock_at_end if self.stock_at_end is not None else (self.end_of_day_stock or 0)
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def __contains__(self, item):
        if item in ["end_of_day_stock", "stock_at_end"]:
            return True
        return hasattr(self, item)

    def get(self, item, default=None):
        if item == "end_of_day_stock":
            return self.end_of_day_stock if self.end_of_day_stock is not None else (self.stock_at_end or 0)
        if item == "stock_at_end":
            return self.stock_at_end if self.stock_at_end is not None else (self.end_of_day_stock or 0)
        return getattr(self, item, default)

class IngestionResult(BaseModel):
    """Résultat global d'une opération d'ingestion."""
    store_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    products_count: int
    sales_count: int
    errors: List[str] = []
