"""
Constants for Auth & Permissions - Michi RBAC
"""
from enum import Enum
from typing import Dict, List

class MichiPermission(str, Enum):
    # Members Management
    MEMBERS_VIEW = "members:view"
    MEMBERS_INVITE = "members:invite"
    MEMBERS_REMOVE = "members:remove"
    MEMBERS_EDIT_ROLE = "members:edit_role"
    
    # Billing & Subscription
    BILLING_VIEW = "billing:view"
    BILLING_MANAGE = "billing:manage"
    
    # Stores & Sources
    STORES_VIEW = "stores:view"
    STORES_MANAGE = "stores:manage"
    
    # Inventory
    INVENTORY_VIEW = "inventory:view"
    INVENTORY_EDIT = "inventory:edit"
    
    # Forecasting
    FORECASTING_VIEW = "forecasting:view"
    FORECASTING_RUN = "forecasting:run"
    
    # General Organization Settings
    SETTINGS_VIEW = "settings:view"
    SETTINGS_EDIT = "settings:edit"

# Default permissions mapping for standard roles
ROLE_PERMISSIONS: Dict[str, List[MichiPermission]] = {
    "admin": list(MichiPermission),
    "manager": [
        MichiPermission.MEMBERS_VIEW,
        MichiPermission.MEMBERS_INVITE,
        MichiPermission.BILLING_VIEW,
        MichiPermission.STORES_VIEW,
        MichiPermission.STORES_MANAGE,
        MichiPermission.INVENTORY_VIEW,
        MichiPermission.INVENTORY_EDIT,
        MichiPermission.FORECASTING_VIEW,
        MichiPermission.FORECASTING_RUN,
        MichiPermission.SETTINGS_VIEW
    ],
    "viewer": [
        MichiPermission.MEMBERS_VIEW,
        MichiPermission.BILLING_VIEW,
        MichiPermission.STORES_VIEW,
        MichiPermission.INVENTORY_VIEW,
        MichiPermission.FORECASTING_VIEW,
        MichiPermission.SETTINGS_VIEW
    ]
}
