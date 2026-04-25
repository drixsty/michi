from functools import wraps
from typing import List, Union
import time
from collections import defaultdict
from core.exceptions import MichiException, UnauthenticatedException, ErrorCode
from modules.auth.domain.permissions import PermissionCode, ROLE_PERMISSIONS
from sqlalchemy import select
import uuid
from loguru import logger
from core.security.plans import PlanName
from core.database.models import Organization, OrganizationMember, UserRole
from modules.auth.domain.access_policy import AccessPolicy

# ── In-memory rate-limit store (TTL dict) ──────────────────────────────────
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

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
                    code=ErrorCode.FORBIDDEN,
                    logging_level="WARNING"
                )
                
            return await f(self, info, *args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: PermissionCode):
    """
    Décorateur pour restreindre l'accès selon une permission granulaire.
    Vérifie les permissions effectives calculées par l'AccessPolicy (Domain).
    """
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
            
            # Fetch rôle et overrides
            stmt = select(OrganizationMember.role, OrganizationMember.permissions).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id
            )
            result = await db.execute(stmt)
            row = result.first()
            
            if not row:
                raise UnauthenticatedException("Session invalide : vous n'êtes plus membre de cette organisation")
            
            user_role_enum, member_perms = row
            user_role = user_role_enum.value if hasattr(user_role_enum, 'value') else str(user_role_enum).lower()
            
            # Calcul des permissions effectives via le DOMAINE
            effective_perms = AccessPolicy.calculate_effective_permissions(user_role, member_perms)
            target_perm = permission.value if hasattr(permission, 'value') else str(permission)
            
            if AccessPolicy.has_permission(effective_perms, target_perm):
                return await f(self, info, *args, **kwargs)

            # Sinon refus
            raise MichiException(
                message=f"Cette action nécessite la permission : {permission}", 
                code=ErrorCode.FORBIDDEN,
                logging_level="WARNING"
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
                raise MichiException(
                    message="Vous n'êtes pas membre de cette organisation", 
                    code=ErrorCode.FORBIDDEN,
                    logging_level="WARNING"
                )
            
            user_role = user_role_enum.value if hasattr(user_role_enum, 'value') else str(user_role_enum).lower()
            
            if user_role not in allowed_roles:
                raise MichiException(
                    message=f"Cette action nécessite un rôle parmi : {', '.join(allowed_roles)}", 
                    code=ErrorCode.FORBIDDEN,
                    logging_level="WARNING"
                )
            
            return await f(self, info, *args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_calls: int, window_seconds: int = 60):
    """
    Décorateur de rate-limiting par utilisateur (in-memory, TTL sliding window).
    
    Args:
        max_calls: Nombre maximum d'appels autorisés dans la fenêtre.
        window_seconds: Durée de la fenêtre de temps en secondes.
    
    Example:
        @rate_limit(max_calls=5, window_seconds=60)  # 5 appels par minute
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(self, info, *args, **kwargs):
            # Clé unique : nom_de_la_fonction + user_id (ou IP fallback)
            user_id = str(info.context.user_id) if info.context.user_id else "anonymous"
            key = f"{f.__name__}:{user_id}"
            
            now = time.monotonic()
            window_start = now - window_seconds
            
            # Nettoyage des timestamps expirés
            _rate_limit_store[key] = [
                ts for ts in _rate_limit_store[key] if ts > window_start
            ]
            
            if len(_rate_limit_store[key]) >= max_calls:
                remaining_wait = int(window_seconds - (now - _rate_limit_store[key][0]))
                logger.warning(f"[RateLimit] BLOCKED {key} — {len(_rate_limit_store[key])}/{max_calls} calls in {window_seconds}s")
                raise MichiException(
                    message=f"Trop de tentatives. Réessayez dans {remaining_wait} secondes.",
                    code=ErrorCode.FORBIDDEN,
                    logging_level="WARNING"
                )
            
            _rate_limit_store[key].append(now)
            logger.debug(f"[RateLimit] {key} — {len(_rate_limit_store[key])}/{max_calls}")
            return await f(self, info, *args, **kwargs)
        return wrapper
    return decorator
