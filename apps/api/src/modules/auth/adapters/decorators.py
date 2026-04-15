from functools import wraps
from typing import List, Union
from exceptions import MichiException, UnauthenticatedException, ErrorCode
from src.modules.auth.infrastructure.models import OrganizationMember, UserRole
from src.modules.auth.domain.constants import MichiPermission, ROLE_PERMISSIONS
from sqlalchemy import select
import uuid
from loguru import logger

def require_permission(permission: MichiPermission):
    """
    Décorateur pour restreindre l'accès selon une permission granulaire.
    Vérifie les permissions explicites (JSON) et les permissions par défaut du rôle.
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(self, info, *args, **kwargs):
            if not info.context.user_id or not info.context.org_id:
                raise UnauthenticatedException("Accès refusé : session ou organisation non identifiée")
                
            db = info.context.db
            user_id = uuid.UUID(str(info.context.user_id))
            org_id = uuid.UUID(str(info.context.org_id))
            
            # 1. Récupérer uniquement le rôle et les permissions (Selective Fetch pour éviter lazy loading)
            result = await db.execute(
                select(OrganizationMember.role, OrganizationMember.permissions).where(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == user_id
                )
            )
            row = result.first()
            
            if not row:
                raise MichiException(message="Vous n'êtes pas membre de cette organisation", code=ErrorCode.FORBIDDEN)
            
            user_role_enum, member_perms = row
            user_role = user_role_enum.value if hasattr(user_role_enum, 'value') else str(user_role_enum).lower()
            
            # L'ADMIN a toujours tous les droits
            if user_role == "admin":
                return await f(self, info, *args, **kwargs)
                
            # Vérifier les overrides explicites (JSONB)
            # ex: {"billing:manage": false} pour retirer un droit par défaut
            member_perms = member_perms or {}
            if permission.value in member_perms:
                if member_perms[permission.value] is True:
                    return await f(self, info, *args, **kwargs)
                elif member_perms[permission.value] is False:
                    logger.warning(f"Accès refusé [Perm Explicit Deny] : User {user_id} tentant {permission}")
                    raise MichiException(message=f"Action refusée : droit '{permission}' révoqué explicitement", code=ErrorCode.FORBIDDEN)

            # Vérifier les permissions par défaut du rôle
            default_perms = ROLE_PERMISSIONS.get(user_role, [])
            if permission in default_perms:
                return await f(self, info, *args, **kwargs)

            # Sinon refus
            logger.warning(f"Accès refusé [Perm Guard] : User {user_id} (Role: {user_role}) n'a pas la permission {permission}")
            raise MichiException(
                message=f"Cette action nécessite la permission : {permission}", 
                code=ErrorCode.FORBIDDEN
            )
            
        return wrapper
    return decorator

def require_role(allowed_roles: Union[str, List[str]]):
    """
    Décorateur classique basé sur le rôle brut.
    Préférer require_permission pour les nouvelles fonctionnalités.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles.lower()]
    else:
        allowed_roles = [r.lower() for r in allowed_roles]

    def decorator(f):
        @wraps(f)
        async def wrapper(self, info, *args, **kwargs):
            if not info.context.user_id or not info.context.org_id:
                raise UnauthenticatedException("Accès refusé : session ou organisation non identifiée")
                
            db = info.context.db
            user_id = uuid.UUID(str(info.context.user_id))
            org_id = uuid.UUID(str(info.context.org_id))
            
            result = await db.execute(
                select(OrganizationMember.role).where(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == user_id
                )
            )
            user_role_enum = result.scalar()
            
            if not user_role_enum:
                raise MichiException(message="Vous n'êtes pas membre de cette organisation", code=ErrorCode.FORBIDDEN)
            
            user_role = user_role_enum.value if hasattr(user_role_enum, 'value') else str(user_role_enum).lower()
            
            if user_role not in allowed_roles:
                raise MichiException(message=f"Cette action nécessite un rôle parmi : {', '.join(allowed_roles)}", code=ErrorCode.FORBIDDEN)
            
            return await f(self, info, *args, **kwargs)
        return wrapper
    return decorator
