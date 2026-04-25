import pytest
from modules.auth.domain.access_policy import AccessPolicy
from modules.auth.domain.permissions import PermissionCode

def test_calculate_effective_permissions_owner():
    """OWNER doit avoir toutes les permissions par défaut."""
    perms = AccessPolicy.calculate_effective_permissions("OWNER")
    # Vérifier quelques permissions clés
    assert PermissionCode.ORG_VIEW.value in perms
    assert PermissionCode.INVENTORY_EDIT.value in perms
    assert PermissionCode.FORECAST_SIMULATE.value in perms

def test_calculate_effective_permissions_viewer():
    """VIEWER doit avoir des permissions restreintes."""
    perms = AccessPolicy.calculate_effective_permissions("VIEWER")
    assert PermissionCode.ORG_VIEW.value in perms
    assert PermissionCode.INVENTORY_VIEW.value in perms
    assert PermissionCode.INVENTORY_EDIT.value not in perms
    assert PermissionCode.ORG_EDIT.value not in perms

def test_permissions_overrides_allow():
    """Un override peut donner une permission supplémentaire."""
    overrides = {PermissionCode.INVENTORY_EDIT.value: True}
    perms = AccessPolicy.calculate_effective_permissions("VIEWER", overrides)
    assert PermissionCode.INVENTORY_EDIT.value in perms

def test_permissions_overrides_deny():
    """Un override peut retirer une permission par défaut."""
    overrides = {PermissionCode.INVENTORY_VIEW.value: False}
    perms = AccessPolicy.calculate_effective_permissions("VIEWER", overrides)
    assert PermissionCode.INVENTORY_VIEW.value not in perms

def test_has_permission_logic():
    """Test de la logique de vérification has_permission."""
    effective = {PermissionCode.ORG_VIEW.value, PermissionCode.INVENTORY_VIEW.value}
    
    assert AccessPolicy.has_permission(effective, PermissionCode.ORG_VIEW.value) is True
    assert AccessPolicy.has_permission(effective, "invalid:perm") is False

def test_role_hierarchy():
    """Test de la hiérarchie des rôles (implicite via les permissions par défaut)."""
    admin_perms = AccessPolicy.calculate_effective_permissions("ADMIN")
    manager_perms = AccessPolicy.calculate_effective_permissions("MANAGER")
    viewer_perms = AccessPolicy.calculate_effective_permissions("VIEWER")
    
    # ADMIN > MANAGER > VIEWER en termes de nombre de permissions
    assert len(admin_perms) >= len(manager_perms)
    assert len(manager_perms) >= len(viewer_perms)
    
    # Vérifier une permission spécifique ADMIN vs VIEWER
    assert PermissionCode.ORG_EDIT.value in admin_perms
    assert PermissionCode.ORG_EDIT.value not in viewer_perms

def test_case_insensitivity_and_handling():
    """Test de la robustesse face à la casse et aux types d'entrée."""
    perms1 = AccessPolicy.calculate_effective_permissions("owner")
    perms2 = AccessPolicy.calculate_effective_permissions("OWNER")
    assert perms1 == perms2
    
    # Rôle inconnu -> viewer par défaut
    perms_unknown = AccessPolicy.calculate_effective_permissions("GHOST")
    perms_viewer = AccessPolicy.calculate_effective_permissions("VIEWER")
    assert perms_unknown == perms_viewer
