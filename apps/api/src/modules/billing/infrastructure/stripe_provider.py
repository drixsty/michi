import stripe
from typing import Optional, List
from datetime import datetime
from loguru import logger

from core.config import settings
from ..domain.ports import IBillingProvider
from ..domain.entities import Invoice, BillingPlan, BillingPlanDefinition

class StripeBillingProvider(IBillingProvider):
    """Implémentation concrète de IBillingProvider utilisant le SDK Stripe"""
    
    def __init__(self):
        self.mode = settings.BILLING_MODE
        if self.mode == "STRIPE":
            stripe.api_key = settings.STRIPE_API_KEY
            
    async def create_customer(self, name: str, email: str, org_id: str) -> Optional[str]:
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
            return customer.id
        except Exception as e:
            logger.error(f"Erreur Stripe (create_customer): {str(e)}")
            return None

    async def create_checkout_session(
        self, customer_id: str, plan: str, success_url: str, cancel_url: str
    ) -> Optional[str]:
        if self.mode == "MOCK":
            logger.info(f"Mode MOCK : Bypass Stripe Checkout pour {customer_id}")
            return success_url

        price_map = {
            "BASIC": settings.STRIPE_PRICE_BASIC,
            "PRO": settings.STRIPE_PRICE_PRO,
            "ENTERPRISE": settings.STRIPE_PRICE_ENTERPRISE
        }
        price_id = price_map.get(plan.upper())
        if not price_id:
            return None

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"plan": plan.upper()}
            )
            return session.url
        except Exception as e:
            logger.error(f"Erreur Stripe (checkout): {str(e)}")
            return None

    async def create_portal_session(self, customer_id: str, return_url: str) -> Optional[str]:
        if self.mode == "MOCK":
            return f"{return_url}?portal_session=mock"

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session.url
        except Exception as e:
            logger.error(f"Erreur Stripe (portal): {str(e)}")
            return None

    async def get_invoices(self, customer_id: str, plan: str) -> List[Invoice]:
        if self.mode == "MOCK":
            return self._get_mock_invoices(plan)

        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=10)
            return [
                Invoice(
                    id=str(inv.id),
                    number=str(inv.number),
                    amount=float(inv.amount_paid) / 100.0,
                    currency=inv.currency.upper() if inv.currency else "",
                    status=str(inv.status).upper() if inv.status else "UNKNOWN",
                    date=datetime.fromtimestamp(inv.created),
                    pdf_url=inv.invoice_pdf if inv.invoice_pdf else None,
                    hosted_url=inv.hosted_invoice_url if inv.hosted_invoice_url else None
                ) for inv in invoices.data
            ]
        except Exception as e:
            logger.error(f"Erreur Stripe (invoices): {str(e)}")
            return []

    async def get_billing_plans(self) -> List["BillingPlanDefinition"]:
        if self.mode == "MOCK":
            return [
                BillingPlanDefinition(
                    id="BASIC", name="Starter", price=99.0, currency="EUR", interval="month",
                    features=["Jusqu'à 50k$/mois de CA", "1 intégration", "Sync quotidienne", "Support email"]
                ),
                BillingPlanDefinition(
                    id="PRO", name="Pro", price=249.0, currency="EUR", interval="month",
                    features=["Jusqu'à 250k$/mois de CA", "Intégrations illimitées", "Sync horaire", "Support prioritaire"],
                    is_popular=True
                ),
                BillingPlanDefinition(
                    id="ENTERPRISE", name="Entreprise", price=0.0, currency="EUR", interval="month",
                    features=["CA illimité", "Délais personnalisés", "API complète", "CSM dédié"]
                )
            ]
        
        try:
            # Simple mock fallback if Stripe doesn't have products yet
            products = stripe.Product.list(active=True)
            plans = []
            for prod in products.data:
                price_id = prod.default_price
                if not price_id:
                    continue
                if isinstance(price_id, str):
                    price = stripe.Price.retrieve(price_id)
                else:
                    price = price_id
                
                plans.append(BillingPlanDefinition(
                    id=prod.metadata.get("plan_id", prod.name.upper()) if prod.metadata else prod.name.upper(),
                    name=prod.name,
                    price=float(price.unit_amount) / 100.0 if getattr(price, 'unit_amount', None) else 0.0,
                    currency=price.currency.upper() if getattr(price, 'currency', None) else "EUR",
                    interval=str(price.recurring.interval) if getattr(price, 'recurring', None) and getattr(price.recurring, 'interval', None) else "month",
                    features=[f.name for f in prod.features if hasattr(f, 'name') and f.name] if hasattr(prod, 'features') and getattr(prod, 'features') else [],
                    is_popular=prod.metadata.get("is_popular", "false").lower() == "true" if prod.metadata else False
                ))
            return plans
        except Exception as e:
            logger.error(f"Erreur Stripe (plans): {str(e)}")
            return []

    def _get_mock_invoices(self, plan: str) -> List[Invoice]:
        if plan.upper() == "BASIC":
            return []
        
        from datetime import timedelta
        import uuid
        now = datetime.now()
        return [
            Invoice(
                id=f"in_mock_{i}",
                number=f"INV-{now.year}-{100-i:03d}",
                amount=49.0 if plan.upper() == "PRO" else 99.0,
                currency="EUR",
                status="PAID",
                date=now - timedelta(days=30*i),
                pdf_url="https://example.com/mock.pdf",
                hosted_url="https://example.com/mock"
            ) for i in range(3)
        ]
