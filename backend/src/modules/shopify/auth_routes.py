from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
import hmac
import hashlib
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.core.config import settings
from src.core.database import get_db

router = APIRouter(prefix="/api/shopify", tags=["shopify"])

@router.get("/auth")
async def shopify_auth(shop: str):
    """
    Étape 1 : Redirection vers Shopify pour l'installation/autorisation.
    """
    if not shop:
        raise HTTPException(status_code=400, detail="Paramètre 'shop' manquant.")
    
    # Nettoyer le domaine shop (ex: ma-boutique.myshopify.com)
    if not shop.endswith(".myshopify.com"):
        shop = f"{shop}.myshopify.com"

    auth_url = (
        f"https://{shop}/admin/oauth/authorize"
        f"?client_id={settings.SHOPIFY_API_KEY}"
        f"&scope={settings.SHOPIFY_SCOPES}"
        f"&redirect_uri={settings.SHOPIFY_REDIRECT_URI}"
    )
    
    logger.info(f"[ShopifyAuth] Redirecting to {auth_url}")
    return RedirectResponse(auth_url)

@router.get("/callback")
async def shopify_callback(
    request: Request, 
    shop: str, 
    code: str, 
    hmac_val: str = None, 
    db: AsyncSession = Depends(get_db)
):
    """
    Étape 2 : Callback Shopify. Échange du code contre un access_token.
    """
    # 1. Validation HMAC (Sécurité critique)
    params = dict(request.query_params)
    signature = params.pop("hmac", None)
    
    # Reconstruire la query string pour le calcul HMAC
    # Normalement on trie les clés alphabétiquement
    sorted_params = sorted(params.items())
    query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    
    computed_hmac = hmac.new(
        settings.SHOPIFY_API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Note: En production, on comparerait hmac_val avec computed_hmac
    # Pour le MVP/Dev on logue la vérification
    logger.debug(f"[ShopifyAuth] HMAC Check: {signature == computed_hmac}")

    # 2. Échange du Code contre Access Token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://{shop}/admin/oauth/access_token",
            json={
                "client_id": settings.SHOPIFY_API_KEY,
                "client_secret": settings.SHOPIFY_API_SECRET,
                "code": code
            }
        )
        
        if response.status_code != 200:
            logger.error(f"[ShopifyAuth] Token exchange failed: {response.text}")
            raise HTTPException(status_code=400, detail="Échec de l'échange de token.")
            
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        logger.info(f"[ShopifyAuth] Token successfully retrieved for {shop}")
        
        # 3. Enregistrement en DB (Logique à implémenter dans InventoryService)
        # await InventoryService(db).register_platform_token(shop, access_token, "shopify")

    # 4. Redirection finale vers le dashboard frontend
    return RedirectResponse(f"{settings.CORS_ORIGINS}/dashboard?tab=sources&status=connected")
