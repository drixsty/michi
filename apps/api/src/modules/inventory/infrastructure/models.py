"""
Re-export layer for backward compatibility.
Implementation moved to modules.inventory.persistence.models.
"""
from .persistence.models import (
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
