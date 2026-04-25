from enum import Enum
from typing import List

class PermissionCode(str, Enum):
    """
    Source de vérité unique pour tous les codes de permission Michi 道.
    Utilisé dans tous les modules : auth, inventory, forecasting, billing, shopify.
    
    Hiérarchie des rôles : VIEWER < MANAGER < ADMIN < OWNER
    """
    # ORGANISATION
    ORG_VIEW            = "org:view"
    ORG_EDIT            = "org:edit"
    ORG_MANAGE_MEMBERS  = "org:manage_members"
    ORG_BILLING         = "org:billing"
    ORG_EXPORT          = "org:export"
    ORG_DELETE          = "org:delete"
    ORG_AUDIT           = "org:audit"

    # MEMBRES
    MEMBERS_VIEW        = "members:view"
    MEMBERS_INVITE      = "members:invite"
    MEMBERS_REMOVE      = "members:remove"
    MEMBERS_EDIT_ROLE   = "members:edit_role"

    # INVENTAIRE / PRODUITS
    INVENTORY_VIEW      = "inventory:view"
    INVENTORY_EDIT      = "inventory:edit"
    INVENTORY_DELETE    = "inventory:delete"
    INVENTORY_IMPORT    = "inventory:import"

    # FOURNISSEURS
    SUPPLIER_VIEW       = "supplier:view"
    SUPPLIER_EDIT       = "supplier:edit"
    SUPPLIER_DELETE     = "supplier:delete"

    # PRÉVISIONS / ANALYTICS
    FORECAST_VIEW       = "forecast:view"
    FORECAST_SIMULATE   = "forecast:simulate"
    FORECAST_EXPORT     = "forecast:export"
    FORECAST_RUN        = "forecast:run"

    # STORES / CONNEXIONS
    STORES_VIEW         = "stores:view"
    STORES_MANAGE       = "stores:manage"

    # PARAMÈTRES
    SETTINGS_VIEW       = "settings:view"
    SETTINGS_EDIT       = "settings:edit"
    SETTINGS_MANAGE_APIS = "settings:manage_apis"

    # BILLING
    BILLING_VIEW        = "billing:view"
    BILLING_MANAGE      = "billing:manage"

    # AUDIT
    AUDIT_VIEW          = "audit:view"


# Mapping par défaut des rôles → permissions
# Source de vérité unique — aligné avec la matrice métier Michi 道
ROLE_PERMISSIONS: dict[str, List[str]] = {
    # OWNER : accès total sans restriction
    "OWNER": [p.value for p in PermissionCode],

    # ADMIN : tout sauf suppression org et audit avancé
    "ADMIN": [
        PermissionCode.ORG_VIEW.value,
        PermissionCode.ORG_EDIT.value,
        PermissionCode.ORG_MANAGE_MEMBERS.value,
        PermissionCode.ORG_BILLING.value,
        PermissionCode.ORG_EXPORT.value,
        PermissionCode.MEMBERS_VIEW.value,
        PermissionCode.MEMBERS_INVITE.value,
        PermissionCode.MEMBERS_REMOVE.value,
        PermissionCode.MEMBERS_EDIT_ROLE.value,
        PermissionCode.INVENTORY_VIEW.value,
        PermissionCode.INVENTORY_EDIT.value,
        PermissionCode.INVENTORY_DELETE.value,
        PermissionCode.INVENTORY_IMPORT.value,
        PermissionCode.SUPPLIER_VIEW.value,
        PermissionCode.SUPPLIER_EDIT.value,
        PermissionCode.SUPPLIER_DELETE.value,
        PermissionCode.FORECAST_VIEW.value,
        PermissionCode.FORECAST_SIMULATE.value,
        PermissionCode.FORECAST_EXPORT.value,
        PermissionCode.FORECAST_RUN.value,
        PermissionCode.STORES_VIEW.value,
        PermissionCode.STORES_MANAGE.value,
        PermissionCode.SETTINGS_VIEW.value,
        PermissionCode.SETTINGS_EDIT.value,
        PermissionCode.SETTINGS_MANAGE_APIS.value,
        PermissionCode.BILLING_VIEW.value,
        PermissionCode.BILLING_MANAGE.value,
        PermissionCode.AUDIT_VIEW.value,
    ],

    # MANAGER : peut éditer l'inventaire et lancer des prédictions, pas de gestion org/membres
    "MANAGER": [
        PermissionCode.ORG_VIEW.value,
        PermissionCode.MEMBERS_VIEW.value,
        PermissionCode.INVENTORY_VIEW.value,
        PermissionCode.INVENTORY_EDIT.value,
        PermissionCode.INVENTORY_IMPORT.value,
        PermissionCode.SUPPLIER_VIEW.value,
        PermissionCode.SUPPLIER_EDIT.value,
        PermissionCode.FORECAST_VIEW.value,
        PermissionCode.FORECAST_SIMULATE.value,
        PermissionCode.FORECAST_RUN.value,
        PermissionCode.STORES_VIEW.value,
        PermissionCode.SETTINGS_VIEW.value,
    ],

    # VIEWER : lecture seule sur tout
    "VIEWER": [
        PermissionCode.ORG_VIEW.value,
        PermissionCode.MEMBERS_VIEW.value,
        PermissionCode.INVENTORY_VIEW.value,
        PermissionCode.SUPPLIER_VIEW.value,
        PermissionCode.FORECAST_VIEW.value,
        PermissionCode.STORES_VIEW.value,
        PermissionCode.SETTINGS_VIEW.value,
    ],
}
