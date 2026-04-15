from fastapi import APIRouter, Request, Header, Depends
from loguru import logger
import stripe

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
    """
    if not stripe_signature:
        return {"error": "Missing signature"}, 400

    payload = await request.body()
    
    # Injection manuelle dans le routeur (Adapter) pour le moment
    # Ou via une dépendance FastAPI si préféré
    provider = StripeBillingProvider()
    repo = SQLAlchemyBillingRepository(db)
    billing_service = ApplicationBillingService(provider, repo)

    try:
        # Note: Le parsing de l'event est complexe car il nécessite le SDK.
        # Idéalement, StripeBillingProvider.parse_webhook_event(payload, signature)
        result = await billing_service.handle_webhook_event(
            payload=payload,
            sig_header=stripe_signature
        )
        return result
    except stripe.error.SignatureVerificationError:
        return {"error": "Invalid signature"}, 400
    except Exception as e:
        logger.error(f"Erreur Webhook : {str(e)}")
        return {"error": "Internal error"}, 500
