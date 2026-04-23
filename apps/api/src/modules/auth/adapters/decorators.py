from functools import wraps
from typing import List, Union
from core.exceptions import MichiException, UnauthenticatedException, ErrorCode
from modules.auth.domain.constants import MichiPermission, ROLE_PERMISSIONS
from sqlalchemy import select
import uuid
from loguru import logger
from core.security.plans import PlanName
from core.database.models import Organization, OrganizationMember, UserRole

def require_plan(min_plan: PlanName):
    """
    Décorateur pour restreindre l'accès selon le plan de l'organisation.
    Vérifie que l'organisation a au moins le plan spécifié.
    Ordre de priorité : FREE < PRO < ENTERPRISE
    """
    plan_hierarchy = {PlanName.FREE: 0, PlanName.PRO: 1, PlanName.ENTERPRISE: 2}
    min_rank = plan_hierarchy.get(min_plan, 0)

    def decorator(f):
        @wraps(f)
        async def wrapper(self, info, *args, **kwargs):
            if not info.context.org_id:
                raise UnauthenticatedException("Action refusée : aucune organisation active.")
                
            db = info.context.db
            org_id = uuid.UUID(str(info.context.org_id))
            
            # Récupérer l'organisation pour vérifier son plan
            stmt = select(Organization.plan).where(Organization.id == org_id)
            result = await db.execute(stmt)
            plan_str = result.scalar()
            
            if not plan_str:
                current_plan = PlanName.FREE
            else:
                try:
                    current_plan = PlanName(plan_str.upper())
                except ValueError:
                    current_plan = PlanName.FREE
            
            current_rank = plan_hierarchy.get(current_plan, 0)
            
            if current_rank < min_rank:
                logger.warning(f"Plan Denied: Org {org_id} has {current_plan}, needs {min_plan}")
                raise MichiException(
                    message=f"Cette fonctionnalité nécessite le plan {min_plan} (Votre plan actuel : {current_plan})", 
                    code=ErrorCode.FORBIDDEN
                )
                
            return await f(self, info, *args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: MichiPermission):
    """
    Décorateur pour restreindre l'accès selon une permission granulaire.
    Vérifie les permissions explicites (JSON) et les permissions par défaut du rôle.
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(self, info, *args, **kwargs):
            if not info.context.user_id:
                raise UnauthenticatedException("Accès refusé : session expirée ou non identifiée")
            if not info.context.org_id:
                # Si l'utilisateur est là mais pas l'org, c'est souvent un problème de switch d'org ou d'onboarding
                raise UnauthenticatedException("Accès refusé : aucune organisation sélectionnée")
                
            db = info.context.db
            user_id = uuid.UUID(str(info.context.user_id))
            org_id = uuid.UUID(str(info.context.org_id))
            
            # 1. Récupérer uniquement le rôle et les permissions (Selective Fetch)
            # Utilisation de scalar pour être plus atomique et profiter du verrouillage du wrapper
            stmt = select(OrganizationMember.role, OrganizationMember.permissions).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id
            )
            result = await db.execute(stmt)
            row = result.first()
            
            if not row:
                logger.warning(f"Access Denied: OrgMember not found (Org: {org_id}, User: {user_id})")
                raise MichiException(message="Vous n'êtes pas membre de cette organisation", code=ErrorCode.FORBIDDEN)
            
            logger.debug(f"Auth Success: User {user_id} in Org {org_id} (Role: {row[0]})")
            
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
            if not info.context.user_id:
                raise UnauthenticatedException("Accès refusé : session expirée ou non identifiée")
            if not info.context.org_id:
                raise UnauthenticatedException("Accès refusé : aucune organisation sélectionnée")
                
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
