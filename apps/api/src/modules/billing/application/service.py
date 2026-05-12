from core.database.models import Organization, User, OrganizationMember
from typing import Optional, List
from loguru import logger
import uuid

from ..domain.ports import IBillingProvider, IBillingRepository
from ..domain.entities import Invoice, BillingPlan, SubscriptionStatus

class ApplicationBillingService:
    """
    Service applicatif pour la gestion de la facturation.
    Implémente les cas d'utilisation métier sans dépendance d'infrastructure.
    """
    
    def __init__(self, provider: IBillingProvider, repository: IBillingRepository):
        self._provider = provider
        self._repo = repository
    
    async def create_customer(self, name: str, email: str, org_id: str) -> Optional[str]:
        """Crée un client Stripe pour une nouvelle organisation"""
        customer_id = await self._provider.create_customer(
            name=name,
            email=email,
            org_id=org_id
        )
        
        if customer_id:
            await self._repo.update_org_billing_info(org_id, customer_id=customer_id, plan=None, status=None)
            
        return customer_id
    
    async def create_customer_if_missing(self, org_id: str) -> Optional[str]:
        """Assure qu'un client Stripe existe pour l'organisation"""
        sub = await self._repo.get_org_billing_info(org_id)
        if sub and sub.customer_id:
            return sub.customer_id
            
        # Récupérer les infos pour la création
        email = await self._repo.get_org_admin_email(org_id)
        # On pourrait aussi avoir besoin du nom de l'org, mais on peut mocker/fallback
        customer_id = await self._provider.create_customer(
            name=f"Org {org_id[:8]}",
            email=email or "",
            org_id=org_id
        )
        
        if customer_id:
            await self._repo.update_org_billing_info(org_id, customer_id=customer_id, plan=None, status=None)
            
        return customer_id

    async def create_checkout_session(self, org_id: str, plan: str, success_url: str, cancel_url: str) -> Optional[str]:
        customer_id = await self.create_customer_if_missing(org_id)
        if not customer_id:
            return None
            
        url = await self._provider.create_checkout_session(
            customer_id=customer_id,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url
        )

        # Sprint 22 : En mode MOCK, on simule l'effet du webhook immédiatement
        # pour éviter que l'utilisateur ne soit bloqué dans une boucle sur la page pricing.
        from core.config.settings import settings
        if settings.BILLING_MODE == "MOCK" and url == success_url:
            logger.info(f"[Mock] Auto-upgrading org {org_id} to {plan} since we are in MOCK mode")
            await self.mock_upgrade_organization(org_id, plan)
            
        return url

    async def create_portal_session(self, org_id: str, return_url: str) -> Optional[str]:
        customer_id = await self.create_customer_if_missing(org_id)
        if not customer_id:
            return None
            
        return await self._provider.create_portal_session(customer_id, return_url)

    async def get_invoices(self, org_id: str) -> List[Invoice]:
        sub = await self._repo.get_org_billing_info(org_id)
        if not sub or not sub.customer_id:
            return []
            
        return await self._provider.get_invoices(sub.customer_id, sub.plan.value)

    async def get_billing_plans(self) -> List["BillingPlanDefinition"]:
        return await self._provider.get_billing_plans()

    async def handle_webhook_event(self, payload: bytes, sig_header: str) -> dict:
        """
        Note: Cette méthode est complexe car elle dépend souvent de signatures spécifiques au provider.
        Dans une architecture hexagonale parfaite, l'adapter REST (router) valide la signature
        via le provider, puis appelle le service avec un événement typé du domaine.
        
        Pour le moment, nous passons par le provider pour le parsing.
        """
        # Logic d'orchestration pour les webhooks...
        # Pour le MVP, on garde une approche simplifiée
        return {"status": "success"}

    async def mock_upgrade_organization(self, org_id: str, plan: str) -> bool:
        """Utilisé uniquement pour le développement / démos"""
        return await self._repo.update_org_billing_info(
            org_id=org_id, 
            customer_id=None, 
            plan=plan, 
            status=SubscriptionStatus.ACTIVE.value
        )
