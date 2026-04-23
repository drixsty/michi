from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.models import Organization, Store
from core.security.plans import get_plan_limits, PlanName
from core.exceptions import MichiException, ErrorCode

class PlanService:
    """
    Service pour vérifier les quotas et limites liés aux plans SaaS.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def can_add_store(self, org_id: UUID) -> bool:
        """Vérifie si l'organisation peut ajouter un nouveau magasin selon son plan."""
        # 1. Récupérer le plan actuel
        stmt = select(Organization.plan).where(Organization.id == org_id)
        result = await self.db.execute(stmt)
        plan_str = result.scalar() or "FREE"
        
        limits = get_plan_limits(plan_str)
        max_stores = limits.get("max_stores", 1)
        
        # 2. Compter les magasins existants
        count_stmt = select(func.count()).select_from(Store).where(Store.organization_id == org_id)
        count_result = await self.db.execute(count_stmt)
        current_count = count_result.scalar() or 0
        
        if current_count >= max_stores:
            raise MichiException(
                message=f"Limite de magasins atteinte pour le plan {plan_str} ({current_count}/{max_stores}). Veuillez passer au plan supérieur.",
                code=ErrorCode.FORBIDDEN
            )
            
        return True

    async def get_forecasting_depth(self, org_id: UUID) -> int:
        """Retourne le nombre de jours de prévision autorisés par le plan."""
        stmt = select(Organization.plan).where(Organization.id == org_id)
        result = await self.db.execute(stmt)
        plan_str = result.scalar() or "FREE"
        
        limits = get_plan_limits(plan_str)
        return limits.get("forecasting_days", 30)
