"""
DEPRECATED — Ce fichier est conservé pour rétrocompatibilité uniquement.
Utiliser modules.auth.domain.permissions.PermissionCode à la place.
"""
from modules.auth.domain.permissions import PermissionCode as MichiPermission, ROLE_PERMISSIONS

__all__ = ["MichiPermission", "ROLE_PERMISSIONS"]
