from functools import wraps
import strawberry
from typing import List, Union
import time
from collections import defaultdict
from core.exceptions import MichiException, UnauthenticatedException, ErrorCode
from modules.auth.domain.permissions import PermissionCode
from sqlalchemy import select
import uuid
from loguru import logger
from core.security.plans import PlanName
from core.database.models import Organization, OrganizationMember
from modules.auth.domain.access_policy import AccessPolicy

# ── Fallback in-memory store (mono-instance uniquement) ───────────────────────
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

# ── Script Lua pour sliding window atomique côté Redis ────────────────────────
# Garantit l'atomicité entre le nettoyage des timestamps expirés et l'ajout du nouveau.
_RATE_LIMIT_LUA = """
local key      = KEYS[1]
local now      = tonumber(ARGV[1])
local window   = tonumber(ARGV[2])
local max_calls = tonumber(ARGV[3])
local ttl      = tonumber(ARGV[4])

local cutoff = now - window

-- Supprimer les entrées hors fenêtre
redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)

-- Compter les appels restants dans la fenêtre
local count = redis.call('ZCARD', key)

if count >= max_calls then
    -- Retourner le temps restant avant le prochain slot libre
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    if #oldest > 0 then
        return tostring(math.ceil(window - (now - tonumber(oldest[2]))))
    end
    return tostring(window)
end

-- Enregistrer l'appel courant (score = timestamp en ms)
redis.call('ZADD', key, now, tostring(now) .. ':' .. tostring(math.random(1, 1000000)))
redis.call('PEXPIRE', key, ttl)
return '0'
"""


async def _redis_rate_limit(key: str, max_calls: int, window_seconds: int) -> int | None:
    """
    Vérifie et incrémente le compteur de rate limit dans Redis.
    Retourne None si l'appel est autorisé, sinon le nombre de secondes d'attente.
    Bascule silencieusement sur le fallback in-memory si Redis est indisponible.
    """
    try:
        from core.infrastructure.redis_client import get_redis
        r = await get_redis()
        now_ms = int(time.time() * 1000)
        window_ms = window_seconds * 1000
        ttl_ms = window_ms + 1000  # TTL légèrement supérieur à la fenêtre

        script = r.register_script(_RATE_LIMIT_LUA)
        result = await script(
            keys=[f"rl:{key}"],
            args=[str(now_ms), str(window_ms), str(max_calls), str(ttl_ms)],
        )
        wait = int(result)
        return wait if wait > 0 else None

    except Exception as e:
        logger.warning(f"[RateLimit] Redis unavailable ({e}), falling back to in-memory")
        return _in_memory_rate_limit(key, max_calls, window_seconds)


def _in_memory_rate_limit(key: str, max_calls: int, window_seconds: int) -> int | None:
    """Fallback in-memory — valide uniquement en mono-instance."""
    now = time.monotonic()
    window_start = now - window_seconds
    _rate_limit_store[key] = [ts for ts in _rate_limit_store[key] if ts > window_start]

    if len(_rate_limit_store[key]) >= max_calls:
        wait = int(window_seconds - (now - _rate_limit_store[key][0]))
        return max(wait, 1)

    _rate_limit_store[key].append(now)
    return None


def require_plan(min_plan: PlanName):
    """
    Décorateur pour restreindre l'accès selon le plan de l'organisation.
    Ordre de priorité : FREE < PRO < ENTERPRISE
    """
    plan_hierarchy = {PlanName.FREE: 0, PlanName.PRO: 1, PlanName.ENTERPRISE: 2}
    min_rank = plan_hierarchy.get(min_plan, 0)

    def decorator(f):
        @wraps(f)
        async def wrapper(self, info: strawberry.types.Info, *args, **kwargs):
            if not info.context.org_id:
                raise UnauthenticatedException("Action refusée : aucune organisation active.")

            db = info.context.db
            org_id = uuid.UUID(str(info.context.org_id))

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
        async def wrapper(self, info: strawberry.types.Info, *args, **kwargs):
            if not info.context.user_id:
                raise UnauthenticatedException("Accès refusé : session expirée ou non identifiée")
            if not info.context.org_id:
                raise UnauthenticatedException("Accès refusé : aucune organisation sélectionnée")

            db = info.context.db
            user_id = uuid.UUID(str(info.context.user_id))
            org_id = uuid.UUID(str(info.context.org_id))

            # --- SUPPORT IMPERSONATION CHECK ---
            from core.database.constants import UserRole
            from core.database.models import OrganizationMember
            
            support_stmt = select(OrganizationMember.user_id).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.role == UserRole.SUPPORT
            )
            support_result = await db.execute(support_stmt)
            is_support = support_result.scalar() is not None

            if is_support:
                from core.database.models import SupportAuditLog
                from core.database.session import session_flow_id
                
                # Enregistrer l'action d'impersonation dans les logs d'audit
                audit_log = SupportAuditLog(
                    support_user_id=user_id,
                    impersonated_org_id=org_id,
                    action=f"graphql:{f.__name__}",
                    flow_id=session_flow_id.get()
                )
                db.add(audit_log)
                await db.flush() # Enregistrer dans la transaction active
                
                from modules.auth.domain.permissions import ROLE_PERMISSIONS
                
                # Récupérer les permissions du rôle SUPPORT
                effective_perms = AccessPolicy.calculate_effective_permissions("support", {})
                target_perm = permission.value if hasattr(permission, 'value') else str(permission)
                
                if AccessPolicy.has_permission(effective_perms, target_perm):
                    return await f(self, info, *args, **kwargs)
                
                raise MichiException(
                    message=f"Cette action nécessite la permission support : {permission}",
                    code=ErrorCode.FORBIDDEN,
                    logging_level="WARNING"
                )
            # ------------------------------------

            stmt = select(
                OrganizationMember.role,
                OrganizationMember.permissions,
                Organization.subscription_status,
                Organization.trial_ends_at
            ).join(
                Organization, OrganizationMember.organization_id == Organization.id
            ).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id
            )
            result = await db.execute(stmt)
            row = result.first()

            if not row:
                raise UnauthenticatedException("Session invalide : vous n'êtes plus membre de cette organisation")

            user_role_enum, member_perms, sub_status, trial_ends_at = row

            from datetime import datetime, timezone
            if sub_status == "TRIALING" and trial_ends_at:
                now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
                end_utc = trial_ends_at.replace(tzinfo=None)
                if now_utc > end_utc and permission not in [PermissionCode.BILLING_MANAGE, PermissionCode.BILLING_VIEW]:
                    raise MichiException(
                        message="Votre période d'essai est terminée. Veuillez choisir un plan pour continuer.",
                        code=ErrorCode.FORBIDDEN,
                        logging_level="WARNING"
                    )

            user_role = user_role_enum.value if hasattr(user_role_enum, 'value') else str(user_role_enum).lower()

            effective_perms = AccessPolicy.calculate_effective_permissions(user_role, member_perms)
            target_perm = permission.value if hasattr(permission, 'value') else str(permission)

            if AccessPolicy.has_permission(effective_perms, target_perm):
                return await f(self, info, *args, **kwargs)

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
        async def wrapper(self, info: strawberry.types.Info, *args, **kwargs):
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
    Décorateur de rate-limiting distribué par utilisateur (Redis sliding window).
    Bascule automatiquement sur un fallback in-memory si Redis est indisponible.

    Args:
        max_calls: Nombre maximum d'appels dans la fenêtre.
        window_seconds: Durée de la fenêtre en secondes.

    Example:
        @rate_limit(max_calls=5, window_seconds=60)
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(self, info: strawberry.types.Info, *args, **kwargs):
            user_id = str(info.context.user_id) if info.context.user_id else "anonymous"
            key = f"{f.__name__}:{user_id}"

            wait = await _redis_rate_limit(key, max_calls, window_seconds)

            if wait is not None:
                logger.warning(
                    f"[RateLimit] BLOCKED {key} — retry in {wait}s "
                    f"(limit: {max_calls}/{window_seconds}s)"
                )
                raise MichiException(
                    message=f"Trop de tentatives. Réessayez dans {wait} secondes.",
                    code=ErrorCode.FORBIDDEN,
                    logging_level="WARNING"
                )

            return await f(self, info, *args, **kwargs)
        return wrapper
    return decorator
