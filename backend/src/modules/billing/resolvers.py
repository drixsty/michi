import strawberry
import uuid
from typing import List
from sqlalchemy import select
from src.core.exceptions import UnauthenticatedException, MichiException, ErrorCode
from src.modules.auth.models import Organization
from src.modules.auth.decorators import require_role
from .types import InvoiceType

@strawberry.type
class BillingQuery:
    @strawberry.field
    async def invoices(self, info) -> List[InvoiceType]:
        """Récupère l'historique des factures de l'organisation."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
            
        db = info.context.db
        billing_service = info.context.billing
        
        # Récupérer l'org pour avoir le stripe_customer_id et le plan actuel
        result = await db.execute(
            select(Organization).where(Organization.id == uuid.UUID(str(info.context.org_id)))
        )
        org = result.scalar_one_or_none()
        
        if not org or not org.stripe_customer_id:
            return []
            
        invoices_data = await billing_service.get_invoices(
            customer_id=org.stripe_customer_id,
            plan=org.plan
        )
        
        return [InvoiceType(**inv) for inv in invoices_data]

@strawberry.type
class BillingMutation:
    @strawberry.mutation
    async def create_checkout_session(self, info, plan: str, success_url: str, cancel_url: str) -> str:
        # ... logic existante ...
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
            
        db = info.context.db
        billing_service = info.context.billing
        
        if not billing_service:
            raise MichiException(message="Service Billing non disponible", code=ErrorCode.INTERNAL_ERROR)
            
        # 1. Récupérer stripe_customer_id de l'organisation
        result = await db.execute(
            select(Organization).where(Organization.id == uuid.UUID(str(info.context.org_id)))
        )
        org = result.scalar_one_or_none()
        
        if not org or not org.stripe_customer_id:
            # Fallback : Création du client si manquant
            user_id = info.context.user_id
            from src.modules.auth.models import User
            user_result = await db.execute(select(User).where(User.id == uuid.UUID(str(user_id))))
            user = user_result.scalar_one_or_none()
            
            customer_id = await billing_service.create_customer(
                name=org.name if org else "Org Michi",
                email=user.email if user else "",
                org_id=str(info.context.org_id)
            )
            if org and customer_id:
                org.stripe_customer_id = customer_id
                await db.flush()
        else:
            customer_id = org.stripe_customer_id
            
        # 2. Créer la session
        if billing_service.mode == "MOCK":
            await billing_service.mock_upgrade_organization(db, str(info.context.org_id), plan)
            return success_url

        url = await billing_service.create_checkout_session(
            customer_id=customer_id,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if not url:
            raise MichiException(message="Impossible de générer le lien de paiement", code=ErrorCode.INTERNAL_ERROR)
            
        return url

    @strawberry.mutation
    @require_role(["admin"])
    async def create_billing_portal_session(self, info, return_url: str) -> str:
        """Crée une session pour le portail de gestion Stripe."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
            
        db = info.context.db
        billing_service = info.context.billing
        
        result = await db.execute(
            select(Organization).where(Organization.id == uuid.UUID(str(info.context.org_id)))
        )
        org = result.scalar_one_or_none()
        
        if not org:
            raise MichiException(message="Organisation non trouvée", code=ErrorCode.NOT_FOUND)

        customer_id = org.stripe_customer_id
        
        if not customer_id:
            # Création à la volée du client (notamment pour le mode MOCK)
            from src.modules.auth.models import User
            user_result = await db.execute(select(User).where(User.id == uuid.UUID(str(info.context.user_id))))
            user = user_result.scalar_one_or_none()
            
            customer_id = await billing_service.create_customer(
                name=org.name,
                email=user.email if user else "",
                org_id=str(info.context.org_id)
            )
            if customer_id:
                org.stripe_customer_id = customer_id
                await db.commit()
                logger.info(f"Stripe Customer auto-créé : {customer_id} pour le portail")
        
        if not customer_id:
            raise MichiException(message="Impossible de créer un compte client Stripe", code=ErrorCode.INTERNAL_ERROR)
            
        url = await billing_service.create_portal_session(
            customer_id=customer_id,
            return_url=return_url
        )
        
        if not url:
            raise MichiException(message="Impossible de générer le lien vers le portail", code=ErrorCode.INTERNAL_ERROR)
            
        return url
