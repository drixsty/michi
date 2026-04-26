from functools import wraps
import strawberry
from core.exceptions import SubscriptionRequiredException, UnauthenticatedException
from core.database.models import Organization
from sqlalchemy import select
import uuid
from loguru import logger

def require_plan(min_plan: str):
    """
    Décorateur pour restreindre l'accès à un résolveur GraphQL selon le plan de l'organisation.
    
    Usage:
        @require_plan("PRO")
        async def my_resolver(self, info: strawberry.types.Info): ...
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(self, info: strawberry.types.Info, *args, **kwargs):
            if not info.context.org_id:
                raise UnauthenticatedException("Contexte d'organisation manquant")
                
            db = info.context.db
            org_id = uuid.UUID(str(info.context.org_id))
            
            # 1. Récupérer le plan de l'organisation
            result = await db.execute(
                select(Organization).where(Organization.id == org_id)
            )
            org = result.scalar_one_or_none()
            
            if not org:
                raise UnauthenticatedException("Organisation non trouvée")
            
            # 2. Vérification du statut et du niveau de plan
            # Hiérarchie simple: ENTERPRISE > PRO > BASIC
            plan_hierarchy = {"BASIC": 0, "PRO": 1, "ENTERPRISE": 2}
            org_plan_level = plan_hierarchy.get(org.plan.upper(), 0)
            required_level = plan_hierarchy.get(min_plan.upper(), 0)
            
            if org.subscription_status.upper() != "ACTIVE" and org_plan_level > 0:
                 logger.warning(f"Accès refusé pour Org {org_id} : Plan {org.plan} mais statut {org.subscription_status}")
                 raise SubscriptionRequiredException(f"Votre abonnement {org.plan} est {org.subscription_status.lower()}. Merci de régulariser votre paiement.")

            if org_plan_level < required_level:
                logger.info(f"Accès refusé pour Org {org_id} (Plan: {org.plan}, Requis: {min_plan})")
                raise SubscriptionRequiredException(f"Cette fonctionnalité nécessite un plan {min_plan} ou supérieur.")
            
            return await f(self, info, *args, **kwargs)
        return wrapper
    return decorator
