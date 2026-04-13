from fastapi import APIRouter, Request, Header, Depends
from src.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from .service import BillingService
from src.core.exceptions import MichiException
from loguru import logger
import stripe

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
        logger.error("Signature Stripe manquante dans les headers")
        return {"error": "Missing signature"}, 400

    payload = await request.body()
    billing_service = BillingService()

    try:
        result = await billing_service.handle_webhook_event(
            payload=payload,
            sig_header=stripe_signature,
            db=db
        )
        return result
    except stripe.error.SignatureVerificationError:
        return {"error": "Invalid signature"}, 400
    except Exception as e:
        logger.error(f"Erreur interne lors du traitement du webhook : {str(e)}")
        return {"error": "Internal error"}, 500
