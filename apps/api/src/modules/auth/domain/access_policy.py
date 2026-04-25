from typing import List, Dict, Any, Optional
from .permissions import PermissionCode, ROLE_PERMISSIONS
import json

class AccessPolicy:
    """
    Domain Policy pour le calcul des droits d'accès.
    Strictement indépendant de la DB ou des frameworks (DDD).
    """

    @staticmethod
    def calculate_effective_permissions(
        role: str, 
        overrides: Optional[Dict[str, bool]] = None
    ) -> List[str]:
        """
        Calcule les permissions effectives basées sur le rôle et les surcharges.
        Un OWNER a toujours tout, un ADMIN a ses droits par défaut + surcharges.
        """
        role_upper = role.upper()
        
        # 1. Base du rôle (fallback sur VIEWER si inconnu)
        base_perms = set(ROLE_PERMISSIONS.get(role_upper, ROLE_PERMISSIONS.get("VIEWER", [])))
        
        # 2. Application des surcharges (Overrides)
        if overrides:
            for perm, allowed in overrides.items():
                if allowed:
                    base_perms.add(perm)
                else:
                    if perm in base_perms:
                        base_perms.remove(perm)
                        
        return sorted(list(base_perms))

    @staticmethod
    def has_permission(
        effective_permissions: List[str], 
        required_permission: str
    ) -> bool:
        """Vérifie si une permission spécifique est présente."""
        return required_permission in effective_permissions

    @staticmethod
    def is_at_least(current_role: str, target_role: str) -> bool:
        """
        Vérifie la hiérarchie des rôles.
        OWNER > ADMIN > MANAGER > VIEWER
        """
        hierarchy = ["VIEWER", "MANAGER", "ADMIN", "OWNER"]
        try:
            return hierarchy.index(current_role.upper()) >= hierarchy.index(target_role.upper())
        except ValueError:
            return False
