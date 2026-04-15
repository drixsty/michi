import stripe
from config import settings
from loguru import logger
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid

class BillingService:
    """
    Service de gestion de la monétisation (Stripe).
    Centralise les interactions avec l'API Stripe pour Michi.
    """
    
    def __init__(self):
        if settings.BILLING_MODE == "STRIPE":
            stripe.api_key = settings.STRIPE_API_KEY
        self.mode = settings.BILLING_MODE
    
    async def create_customer(self, name: str, email: str, org_id: str) -> Optional[str]:
        """
        Crée un client dans Stripe pour une organisation Michi.
        
        Args:
            name: Nom de l'organisation.
            email: Email de contact (admin).
            org_id: ID interne Michi de l'organisation.
            
        Returns:
            stripe_customer_id si succès, None sinon.
        """
        if self.mode == "MOCK":
            logger.info(f"Mode MOCK : Simulation de création client Stripe pour {org_id}")
            return f"cus_mock_{org_id[:8]}"

        try:
            customer = stripe.Customer.create(
                name=name,
                email=email,
                metadata={
                    "michi_org_id": org_id,
                    "env": settings.ENVIRONMENT
                }
            )
            logger.info(f"Stripe Customer créé : {customer.id} pour l'organisation {org_id}")
            return customer.id
        except Exception as e:
            logger.error(f"Erreur lors de la création du client Stripe pour {org_id}: {str(e)}")
            return None

    async def get_checkout_url(self, customer_id: str, success_url: str, cancel_url: str, price_id: str) -> Optional[str]:
        """
        Génère une URL de session Checkout pour un abonnement.
        """
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return session.url
        except Exception as e:
            logger.error(f"Erreur lors de la création de la session Checkout : {str(e)}")
            return None

    async def create_checkout_session(self, customer_id: str, plan: str, success_url: str, cancel_url: str) -> Optional[str]:
        """
        Crée une session de Checkout Stripe pour un plan spécifique.
        """
        price_map = {
            "BASIC": settings.STRIPE_PRICE_BASIC,
            "PRO": settings.STRIPE_PRICE_PRO,
            "ENTERPRISE": settings.STRIPE_PRICE_ENTERPRISE
        }
        
        price_id = price_map.get(plan.upper())
        if not price_id:
            logger.error(f"Plan invalide : {plan}")
            return None
            
        if self.mode == "MOCK":
            logger.info(f"Mode MOCK : Bypass Stripe Checkout, retour URL succès pour {customer_id}")
            return success_url

        return await self.get_checkout_url(customer_id, success_url, cancel_url, price_id)

    async def create_portal_session(self, customer_id: str, return_url: str) -> Optional[str]:
        """
        Génère une URL pour le portail de gestion Stripe (Billing Portal).
        """
        if self.mode == "MOCK":
            logger.info(f"Mode MOCK : Simulation du Billing Portal pour {customer_id}")
            # On simule une redirection vers un portail mocké (ou simplement le retour avec un flag)
            return f"{return_url}?portal_session=mock_{uuid.uuid4().hex[:8]}"

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session.url
        except Exception as e:
            logger.error(f"Erreur lors de la création de la session portail : {str(e)}")
            return None

    async def get_invoices(self, customer_id: str, plan: str = "BASIC") -> list:
        """
        Récupère l'historique des factures pour un client.
        """
        if self.mode == "MOCK":
            return self._get_mock_invoices(plan)

        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=10)
            return [{
                "id": inv.id,
                "number": inv.number,
                "amount": inv.amount_paid / 100.0,
                "currency": inv.currency.upper(),
                "status": inv.status.upper(),
                "date": datetime.fromtimestamp(inv.created),
                "pdf_url": inv.invoice_pdf,
                "hosted_url": inv.hosted_invoice_url
            } for inv in invoices.data]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des factures Stripe : {str(e)}")
            return []

    def _get_mock_invoices(self, plan: str):
        """Génère des factures fictives robustes pour le mode MOCK (12 mois)."""
        amount = 49.0 if plan.upper() == "PRO" else 0.0
        if amount == 0:
            return [] # Pas de factures pour le plan BASIC
            
        now = datetime.now()
        invoices = []
        
        for i in range(12):
            invoice_date = now - timedelta(days=30 * i)
            # On simule quelques variations mineures ou des mois avec promos
            current_amount = amount
            if i == 5: current_amount = 0.0 # Un mois offert ?
            
            invoices.append({
                "id": f"in_mock_{i}_{uuid.uuid4().hex[:4]}",
                "number": f"INV-{invoice_date.year}-{100 - i:03d}",
                "amount": current_amount,
                "currency": "EUR",
                "status": "PAID" if current_amount > 0 or i > 0 else "OPEN",
                "date": invoice_date,
                "pdf_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                "hosted_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
            })
            
        return invoices

    async def mock_upgrade_organization(self, db: AsyncSession, org_id: str, plan: str):
        """
        Simule l'effet d'un webhook réussi pour le mode MOCK.
        """
        from src.modules.auth.infrastructure.models import Organization
        from sqlalchemy import select
        import uuid
        
        try:
            target_id = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
            result = await db.execute(select(Organization).where(Organization.id == target_id))
            org = result.scalar_one_or_none()
            if org:
                org.plan = plan.upper()
                org.subscription_status = "ACTIVE"
                await db.commit()
                logger.success(f"[MOCK] Organisation {org_id} upgradée vers {plan}")
                return True
        except Exception as e:
            logger.error(f"[MOCK] Échec de l'upgrade simulé : {str(e)}")
        return False
            
    async def handle_webhook_event(self, payload: bytes, sig_header: str, db: AsyncSession):
        """
        Traite un événement Stripe Webhook et met à jour l'organisation Michi.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Payload invalide : {str(e)}")
            raise e
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Signature Webhook invalide : {str(e)}")
            raise e

        logger.info(f"Webhook Stripe reçu : {event['type']} [{event['id']}]")

        # 1. Gestion de la complétion du Checkout (Premier paiement)
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_id = session.get('customer')
            subscription_id = session.get('subscription')
            
            # Récupérer l'organisation par son stripe_customer_id
            from src.modules.auth.infrastructure.models import Organization
            from sqlalchemy import select
            
            result = await db.execute(
                select(Organization).where(Organization.stripe_customer_id == customer_id)
            )
            org = result.scalar_one_or_none()
            if org:
                # Dans un vrai système, on récupérerait le plan depuis les line_items ou metadata
                # Pour le MVP, on regarde si la session checkout avait des metadata
                plan = session.get('metadata', {}).get('plan', 'BASIC')
                org.plan = plan.upper()
                org.subscription_status = "ACTIVE"
                logger.success(f"Organisation {org.id} passée au plan {org.plan} (Subscription: {subscription_id})")
                await db.commit()

        # 2. Gestion des mises à jour d'abonnement / résiliations
        elif event['type'] in ['customer.subscription.updated', 'customer.subscription.deleted']:
            subscription = event['data']['object']
            customer_id = subscription.get('customer')
            status = subscription.get('status') # active, past_due, canceled, etc.
            
            from src.modules.auth.infrastructure.models import Organization
            from sqlalchemy import select
            
            result = await db.execute(
                select(Organization).where(Organization.stripe_customer_id == customer_id)
            )
            org = result.scalar_one_or_none()
            if org:
                # Map Stripe status to Michi status
                org.subscription_status = status.upper()
                if status == 'canceled':
                    org.plan = "BASIC" # Retour au plan gratuit si annulé
                
                logger.info(f"Abonnement Org {org.id} mis à jour : {org.subscription_status}")
                await db.commit()

        return {"status": "success"}
