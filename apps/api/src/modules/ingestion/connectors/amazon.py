"""
Amazon Seller Central Connector — Michi 道
Intègre l'Amazon Selling Partner API (SP-API) pour synchroniser produits et ventes.

Authentification : LWA (Login with Amazon) OAuth 2.0 — refresh_token flow
API utilisées :
  - FBA Inventory API v1         →  fetch_products() (SKU + stock + titre)
  - Sales API v1 orderMetrics    →  fetch_sales_history() (ventes journalières)

Marketplaces EU supportées :
  - A13V1IB3VIYZZH  →  Amazon.fr
  - A1PA6795UKMFR9  →  Amazon.de
  - APJ6JRA9NG5V4   →  Amazon.it
  - A1RKKUPIHCS9HS  →  Amazon.es
  - A1F83G8C2ARO7P  →  Amazon.co.uk

Note FBA-only : fetch_products() utilise /fba/inventory/v1/summaries qui couvre
uniquement les vendeurs FBA. Pour MFN (Merchant Fulfilled), implémenter le Reports API
(type GET_MERCHANT_LISTINGS_ALL_DATA) dans une future version.

Variables requises (StoreCredential) :
  encrypted_api_key    → lwa_client_id
  encrypted_api_secret → lwa_client_secret
  encrypted_access_token → lwa_refresh_token
  meta.marketplace_id  → ex: A13V1IB3VIYZZH
  meta.seller_id       → Seller ID Amazon (obligatoire pour certains endpoints)
"""

import asyncio
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from core.utils import retry
from ..domain.base import BaseConnector
from ..domain.schemas import IngestedProduct, IngestedSale

# ── Constantes SP-API ─────────────────────────────────────────────────────────

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
SP_API_BASE = "https://sellingpartnerapi-eu.amazon.com"

MARKETPLACE_IDS: Dict[str, str] = {
    "FR": "A13V1IB3VIYZZH",
    "DE": "A1PA6795UKMFR9",
    "IT": "APJ6JRA9NG5V4",
    "ES": "A1RKKUPIHCS9HS",
    "UK": "A1F83G8C2ARO7P",
    "NL": "A1805IZSGTT6HS",
    "BE": "AMEN7PMS3EDWL",
    "PL": "A1C3SOZRARQ6R3",
    "SE": "A2NODRKZP88ZB9",
}

# Rate limits SP-API : 2 req/s pour FBA Inventory, 0.5 req/s pour Sales
_RATE_LIMIT_DELAY = 1.1


class AmazonConnector(BaseConnector):
    """
    Connecteur Amazon SP-API pour Michi.
    Mode mock (USE_MOCK_AMAZON=true) ou production FBA.

    Cache token LWA au niveau de la classe (partagé entre instances)
    pour éviter les refreshes inutiles causés par ConnectorFactory.
    """

    # Cache partagé entre toutes les instances (clé = lwa_client_id[:16])
    _class_token_cache: Dict[str, Any] = {}

    def __init__(self):
        self._use_mock: bool = os.getenv("USE_MOCK_AMAZON", "true").lower() == "true"

    # ── Authentification LWA ──────────────────────────────────────────────────

    async def _get_access_token(self, credentials: Dict[str, Any]) -> str:
        """Obtient ou rafraîchit le token LWA (cache classe, TTL 55 min)."""
        cache_key = credentials.get("lwa_client_id", "")[:16]
        cached = AmazonConnector._class_token_cache.get(cache_key)

        if cached and cached["expires_at"] > time.time():
            return cached["token"]

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                LWA_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": credentials["lwa_refresh_token"],
                    "client_id": credentials["lwa_client_id"],
                    "client_secret": credentials["lwa_client_secret"],
                },
            )
            resp.raise_for_status()
            data = resp.json()

        token = data["access_token"]
        AmazonConnector._class_token_cache[cache_key] = {
            "token": token,
            "expires_at": time.time() + 3300,
        }
        logger.debug(f"[Amazon] LWA token rafraîchi pour client_id={cache_key}...")
        return token

    def _build_headers(self, token: str) -> Dict[str, str]:
        return {
            "x-amz-access-token": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ── Interface BaseConnector ───────────────────────────────────────────────

    async def validate_connection(self, credentials: Dict[str, Any]) -> bool:
        """Valide les credentials via /sellers/v1/marketplaceParticipations."""
        if self._use_mock:
            return True

        required = {"lwa_client_id", "lwa_client_secret", "lwa_refresh_token", "marketplace_id"}
        if not required.issubset(credentials.keys()):
            logger.warning(f"[Amazon] Credentials manquants : {required - credentials.keys()}")
            return False

        try:
            token = await self._get_access_token(credentials)
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{SP_API_BASE}/sellers/v1/marketplaceParticipations",
                    headers=self._build_headers(token),
                )
                resp.raise_for_status()
            logger.info("[Amazon] validate_connection : OK")
            return True
        except Exception as exc:
            logger.error(f"[Amazon] validate_connection échoué : {exc}")
            return False

    @retry(retries=3, delay=_RATE_LIMIT_DELAY)
    async def fetch_products(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedProduct]:
        """
        Récupère tous les articles FBA via /fba/inventory/v1/summaries.
        Pagine avec nextToken jusqu'à épuisement.

        Note : couvre uniquement les produits FBA. Pour MFN, utiliser Reports API.
        """
        if self._use_mock or not credentials:
            return self._mock_products(shop_id)

        marketplace_id = credentials.get("marketplace_id", MARKETPLACE_IDS["FR"])
        token = await self._get_access_token(credentials)
        products: List[IngestedProduct] = []
        next_token: Optional[str] = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params: Dict[str, Any] = {
                    "details": "true",
                    "granularityType": "Marketplace",
                    "granularityId": marketplace_id,
                    "marketplaceIds": marketplace_id,
                }
                if next_token:
                    params["nextToken"] = next_token

                resp = await client.get(
                    f"{SP_API_BASE}/fba/inventory/v1/summaries",
                    headers=self._build_headers(token),
                    params=params,
                )
                resp.raise_for_status()
                body = resp.json().get("payload", {})
                summaries = body.get("inventorySummaries", [])

                for item in summaries:
                    sku = item.get("sellerSku", "")
                    if not sku:
                        continue

                    details = item.get("inventoryDetails", {})
                    qty = int(details.get("fulfillableQuantity", 0))

                    products.append(
                        IngestedProduct(
                            sku=sku,
                            title=item.get("productName") or sku,
                            price=0.0,  # prix non disponible dans l'API Inventory
                            current_stock=qty,
                            vendor="Amazon",
                        )
                    )

                next_token = body.get("nextToken")
                if not next_token:
                    break
                await asyncio.sleep(_RATE_LIMIT_DELAY)

        logger.info(f"[Amazon] fetch_products : {len(products)} SKUs FBA récupérés")
        return products

    @retry(retries=3, delay=_RATE_LIMIT_DELAY)
    async def fetch_sales_history(
        self,
        product_sku: str,
        shop_id: str,
        days: int = 365,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedSale]:
        """
        Récupère l'historique de ventes via /sales/v1/orderMetrics.
        Granularité journalière, filtré par SKU vendeur.

        Limite SP-API : fenêtre max de 2 ans, granularité Day → max 730 entrées.
        """
        if self._use_mock or not credentials:
            return self._mock_sales(product_sku, days)

        token = await self._get_access_token(credentials)
        marketplace_id = credentials.get("marketplace_id", MARKETPLACE_IDS["FR"])

        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=days)
        sales: List[IngestedSale] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{SP_API_BASE}/sales/v1/orderMetrics",
                headers=self._build_headers(token),
                params={
                    "marketplaceIds": marketplace_id,
                    "interval": (
                        f"{start_dt.strftime('%Y-%m-%dT00:00:00Z')}"
                        f"--{end_dt.strftime('%Y-%m-%dT23:59:59Z')}"
                    ),
                    "granularity": "Day",
                    "sku": product_sku,  # filtre par seller SKU (≠ ASIN)
                },
            )
            resp.raise_for_status()
            metrics = resp.json().get("payload", [])

        for metric in metrics:
            interval_start = metric.get("interval", "").split("--")[0]
            try:
                sale_date = datetime.fromisoformat(
                    interval_start.replace("Z", "+00:00")
                ).date()
            except ValueError:
                continue

            units = int(metric.get("unitCount", 0))
            sales.append(
                IngestedSale(
                    sku=product_sku,
                    date=sale_date,
                    units_sold=units,
                )
            )

        logger.info(f"[Amazon] fetch_sales_history : {len(sales)} jours pour SKU={product_sku}")
        return sales

    async def fetch_all_data(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Récupère produits FBA + ventes. Mock si pas de credentials."""
        if self._use_mock or not credentials:
            from modules.shopify.infrastructure.mock_generator import generate_full_mock_dataset
            products_raw, sales_raw = generate_full_mock_dataset(count=50, store_id=shop_id)
            return {
                "products": [
                    IngestedProduct(sku=p["sku"], title=p["title"], current_stock=p["current_stock"])
                    for p in products_raw
                ],
                "sales": [
                    IngestedSale(sku=s.get("sku", ""), date=s["date"], units_sold=int(s["units_sold"]))
                    for s in sales_raw if s.get("sku")
                ],
            }

        products = await self.fetch_products(shop_id, credentials=credentials)
        all_sales: List[IngestedSale] = []
        for product in products:
            sku_sales = await self.fetch_sales_history(
                product.sku, shop_id, credentials=credentials
            )
            all_sales.extend(sku_sales)
            await asyncio.sleep(_RATE_LIMIT_DELAY)

        return {"products": products, "sales": all_sales}

    # ── Données Mock ──────────────────────────────────────────────────────────

    def _mock_products(self, shop_id: str) -> List[IngestedProduct]:
        import random
        rng = random.Random(hash(shop_id) % 10000)
        catalog = [
            ("B0CX1234AB", "T-shirt Basique Blanc", 29.99),
            ("B0CX2345CD", "Jean Slim Bleu", 89.99),
            ("B0CX3456EF", "Sérum Vitamine C 30ml", 34.99),
            ("B0CX4567GH", "Crème Hydratante SPF50", 24.99),
            ("B0CX5678IJ", "Sac à Main Structuré", 129.99),
            ("B0CX6789KL", "Sneakers Blanches", 79.99),
            ("B0CX7890MN", "Mascara Volume Extrême", 19.99),
            ("B0CX8901OP", "Écharpe Cachemire Grise", 149.99),
            ("B0CX9012QR", "Fond de Teint Longue Tenue", 42.99),
            ("B0CX0123ST", "Bracelet Manchette Argenté", 59.99),
        ]
        return [
            IngestedProduct(sku=sku, title=title, price=price,
                            current_stock=rng.randint(0, 300), vendor="Amazon")
            for sku, title, price in catalog
        ]

    def _mock_sales(self, product_sku: str, days: int) -> List[IngestedSale]:
        import random
        rng = random.Random(hash(product_sku))
        today = date.today()
        return [
            IngestedSale(
                sku=product_sku,
                date=today - timedelta(days=days - 1 - i),
                units_sold=max(0, int(rng.gauss(5, 2))),
            )
            for i in range(days)
        ]
