from fastapi import APIRouter, Request, Header, Depends, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
import stripe

from core.config import settings
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from ..application.service import ApplicationBillingService
from ..infrastructure.stripe_provider import StripeBillingProvider
from ..infrastructure.repositories import SQLAlchemyBillingRepository

router = APIRouter(prefix="/api/billing", tags=["Billing"])

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de réception des webhooks Stripe.
    Sécurisé par signature HMAC (STRIPE_WEBHOOK_SECRET).
    Gère : checkout.session.completed → activation du plan.
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    payload = await request.body()
    provider = StripeBillingProvider()
    repo = SQLAlchemyBillingRepository(db)
    billing_service = ApplicationBillingService(provider, repo)

    # En mode MOCK, on ne valide pas la signature
    if settings.BILLING_MODE == "MOCK":
        logger.info("[Webhook] Mode MOCK — signature ignorée")
        return JSONResponse({"status": "mock_ok"})

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("[Webhook] Signature Stripe invalide — rejet")
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as e:
        logger.error(f"[Webhook] Erreur de parsing : {e}")
        raise HTTPException(status_code=400, detail="Webhook parsing error")

    # Traitement des événements
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        org_id = event_data.get("metadata", {}).get("org_id")
        plan = event_data.get("metadata", {}).get("plan", "BASIC").upper()
        customer_id = event_data.get("customer")
        subscription_id = event_data.get("subscription")

        if org_id:
            logger.info(f"[Webhook] checkout.session.completed → org={org_id}, plan={plan}, customer={customer_id}, sub={subscription_id}")
            await repo.update_org_billing_info(
                org_id=org_id,
                customer_id=customer_id,
                plan=plan,
                status="ACTIVE",
                subscription_id=subscription_id
            )
            await db.commit()
        else:
            logger.warning("[Webhook] checkout.session.completed sans org_id dans metadata")

    elif event_type == "customer.subscription.deleted":
        subscription_id = event_data.get("id")
        customer_id = event_data.get("customer")
        if subscription_id:
            logger.info(f"[Webhook] subscription.deleted → sub={subscription_id}")
            # Rétrograder au plan FREE si l'abonnement spécifique est annulé
            org_id = await repo.get_org_id_by_subscription(subscription_id)
            if org_id:
                await repo.update_org_billing_info(
                    org_id=org_id,
                    customer_id=customer_id,
                    plan="BASIC",
                    status="CANCELED",
                    subscription_id=None # On retire la liaison d'abonnement annulé
                )
                await db.commit()
            else:
                logger.warning(f"[Webhook] Aucun org_id trouvé pour l'abonnement {subscription_id}")

    else:
        logger.debug(f"[Webhook] Événement ignoré : {event_type}")

    return JSONResponse({"status": "ok"})
