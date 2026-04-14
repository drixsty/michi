"""
Re-export layer for backward compatibility.
Implementation moved to src.modules.inventory.infrastructure.persistence.models.
"""
from .infrastructure.persistence.models import (
    PlatformSource, 
    Store, 
    Product, 
    Alert, 
    SalesLog, 
    Supplier, 
    AlertEmail, 
    PurchaseOrder
)

__all__ = [
    "PlatformSource",
    "Store",
    "Product",
    "Alert",
    "SalesLog",
    "Supplier",
    "AlertEmail",
    "PurchaseOrder",
]
