from abc import ABC, abstractmethod
from typing import Optional, List
from .entities import Invoice, Subscription, BillingPlan, BillingPlanDefinition

class IBillingProvider(ABC):
    """Port sortant pour le fournisseur de paiement (ex: Stripe)"""
    
    @abstractmethod
    async def create_customer(self, name: str, email: str, org_id: str) -> Optional[str]:
        pass
        
    @abstractmethod
    async def create_checkout_session(
        self, customer_id: str, plan: str, success_url: str, cancel_url: str
    ) -> Optional[str]:
        pass
        
    @abstractmethod
    async def create_portal_session(self, customer_id: str, return_url: str) -> Optional[str]:
        pass
        
    @abstractmethod
    async def get_invoices(self, customer_id: str, plan: str) -> List[Invoice]:
        pass

    @abstractmethod
    async def get_billing_plans(self) -> List["BillingPlanDefinition"]:
        pass

class IBillingRepository(ABC):
    """Port sortant pour la persistence des données de facturation"""
    
    @abstractmethod
    async def get_org_billing_info(self, org_id: str) -> Optional[Subscription]:
        pass
        
    @abstractmethod
    async def update_org_billing_info(self, org_id: str, customer_id: str, plan: str, status: str) -> bool:
        pass
        
    @abstractmethod
    async def get_org_admin_email(self, org_id: str) -> Optional[str]:
        pass
