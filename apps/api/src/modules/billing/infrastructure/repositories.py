from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database.models import Organization, User
from ..domain.ports import IBillingRepository
from ..domain.entities import Subscription, SubscriptionStatus, BillingPlan

class SQLAlchemyBillingRepository(IBillingRepository):
    """Implémentation du repository pour isoler l'accès DB de Billing"""
    
    def __init__(self, db: AsyncSession):
        self._db = db
        
    async def get_org_billing_info(self, org_id: str) -> Optional[Subscription]:
        try:
            target_id = uuid.UUID(org_id)
            result = await self._db.execute(select(Organization).where(Organization.id == target_id))
            org = result.scalar_one_or_none()
            if not org:
                return None
            
            return Subscription(
                customer_id=org.stripe_customer_id,
                plan=BillingPlan(org.plan) if org.plan else BillingPlan.BASIC,
                status=SubscriptionStatus(org.subscription_status) if org.subscription_status else SubscriptionStatus.ACTIVE,
                subscription_id=None # Pas stocké dans org pour le moment
            )
        except Exception:
            return None
            
    async def update_org_billing_info(self, org_id: str, customer_id: str, plan: str, status: str) -> bool:
        try:
            target_id = uuid.UUID(org_id)
            result = await self._db.execute(select(Organization).where(Organization.id == target_id))
            org = result.scalar_one_or_none()
            if not org:
                return False
                
            if customer_id:
                org.stripe_customer_id = customer_id
            if plan:
                org.plan = plan.upper()
            if status:
                org.subscription_status = status.upper()
                
            await self._db.flush()
            return True
        except Exception:
            return False
            
    async def get_org_admin_email(self, org_id: str) -> Optional[str]:
        """Récupère l'email du premier administrateur trouvé pour l'org"""
        from core.database.models import OrganizationMember, UserRole
        try:
            target_id = uuid.UUID(org_id)
            query = (
                select(User.email)
                .join(OrganizationMember, OrganizationMember.user_id == User.id)
                .where(OrganizationMember.organization_id == target_id)
                .where(OrganizationMember.role == UserRole.ADMIN)
                .limit(1)
            )
            result = await self._db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            return None
