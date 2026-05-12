import strawberry
from typing import List
from core.exceptions import MichiException, ErrorCode
from modules.auth.adapters.decorators import require_permission
from modules.auth.domain.constants import MichiPermission
from .types import InvoiceType, BillingPlanType

@strawberry.type
class BillingQuery:
    @strawberry.field
    async def billingPlans(self, info: strawberry.types.Info) -> List[BillingPlanType]:
        """Récupère les plans de facturation disponibles. Requête publique."""
        billing_service = info.context.services.billing_service
        plans_entities = await billing_service.get_billing_plans()
        return [
            BillingPlanType(
                id=p.id,
                name=p.name,
                price=p.price,
                currency=p.currency,
                interval=p.interval,
                features=p.features,
                is_popular=p.is_popular
            ) for p in plans_entities
        ]

    @strawberry.field
    @require_permission(MichiPermission.BILLING_VIEW)
    async def invoices(self, info: strawberry.types.Info) -> List[InvoiceType]:
        """Récupère l'historique des factures de l'organisation."""
        billing_service = info.context.services.billing_service
        org_id = str(info.context.org_id)
        
        invoices_entities = await billing_service.get_invoices(org_id=org_id)
        
        return [
            InvoiceType(
                id=inv.id,
                number=inv.number,
                amount=inv.amount,
                currency=inv.currency,
                status=inv.status,
                date=inv.date,
                pdf_url=inv.pdf_url,
                hosted_url=inv.hosted_url
            ) for inv in invoices_entities
        ]

@strawberry.type
class BillingMutation:
    @strawberry.mutation
    @require_permission(MichiPermission.BILLING_MANAGE)
    async def create_checkout_session(self, info: strawberry.types.Info, plan: str, success_url: str, cancel_url: str) -> str:
        billing_service = info.context.services.billing_service
        org_id = str(info.context.org_id)
        
        url = await billing_service.create_checkout_session(
            org_id=org_id,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        await info.context.db.commit()
        
        if not url:
            raise MichiException(message="Impossible de générer le lien de paiement", code=ErrorCode.INTERNAL_ERROR)
            
        return url

    @strawberry.mutation
    @require_permission(MichiPermission.BILLING_MANAGE)
    async def create_billing_portal_session(self, info: strawberry.types.Info, return_url: str) -> str:
        billing_service = info.context.services.billing_service
        org_id = str(info.context.org_id)
        
        url = await billing_service.create_portal_session(
            org_id=org_id,
            return_url=return_url
        )
        
        await info.context.db.commit()
        
        if not url:
            raise MichiException(message="Impossible de générer le lien vers le portail", code=ErrorCode.INTERNAL_ERROR)
            
        return url
