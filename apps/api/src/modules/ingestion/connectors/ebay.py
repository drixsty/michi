"""
eBay Connector — Michi 道
Intègre les eBay REST APIs pour synchroniser produits et ventes.

Authentification : OAuth 2.0 — Authorization Code + Refresh Token
API utilisées :
  - Sell Inventory API v1          →  fetch_products() (listings actifs)
  - Sell Analytics API v1          →  fetch_sales_history() (traffic report)
  - Sell Fulfillment API v1        →  commandes complétées (fallback ventes)

Scopes OAuth requis :
  - https://api.ebay.com/oauth/api_scope/sell.inventory
  - https://api.ebay.com/oauth/api_scope/sell.analytics.readonly
  - https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly

Variables d'environnement requises (StoreCredential.meta) :
  - ebay_client_id      : App ID eBay
  - ebay_client_secret  : Cert ID eBay
  - ebay_refresh_token  : Refresh Token du vendeur
  - marketplace_id      : EBAY_FR, EBAY_DE, EBAY_GB, EBAY_IT, EBAY_ES (défaut : EBAY_FR)

Mock activé si settings.USE_MOCK_EBAY = True (défaut dev).
"""

import asyncio
import base64
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from core.utils import retry
from ..domain.base import BaseConnector
from ..domain.schemas import IngestedProduct, IngestedSale

# ── Constantes eBay API ───────────────────────────────────────────────────────

EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_API_BASE = "https://api.ebay.com"

EBAY_MARKETPLACES: Dict[str, str] = {
    "FR": "EBAY_FR",
    "DE": "EBAY_DE",
    "UK": "EBAY_GB",
    "IT": "EBAY_IT",
    "ES": "EBAY_ES",
    "NL": "EBAY_NL",
    "BE": "EBAY_BE",
    "PL": "EBAY_PL",
    "AT": "EBAY_AT",
    "CH": "EBAY_CH",
    "US": "EBAY_US",
}

_RATE_LIMIT_DELAY = 0.5  # eBay : ~5 req/s burst


class EbayConnector(BaseConnector):
    """
    Connecteur eBay REST API pour Michi.
    Gère le refresh OAuth automatique et le rate limiting.

    Cache token partagé au niveau classe pour éviter les refreshes inutiles
    causés par ConnectorFactory (nouvelle instance à chaque appel).
    """

    # Cache partagé entre toutes les instances (clé = ebay_client_id[:8])
    _class_token_cache: Dict[str, Any] = {}

    def __init__(self):
        self._use_mock: bool = os.getenv("USE_MOCK_EBAY", "true").lower() == "true"

    # ── Authentification OAuth ────────────────────────────────────────────────

    async def _get_access_token(self, credentials: Dict[str, Any]) -> str:
        """Obtient ou rafraîchit le token OAuth eBay (cache classe, TTL ~2h)."""
        cache_key = credentials.get("ebay_client_id", "")
        cached = EbayConnector._class_token_cache.get(cache_key)

        if cached and cached["expires_at"] > time.time():
            return cached["token"]

        b64_creds = base64.b64encode(
            f"{credentials['ebay_client_id']}:{credentials['ebay_client_secret']}".encode()
        ).decode()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                EBAY_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {b64_creds}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": credentials["ebay_refresh_token"],
                    "scope": " ".join([
                        "https://api.ebay.com/oauth/api_scope/sell.inventory",
                        "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
                        "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
                    ]),
                },
            )
            resp.raise_for_status()
            data = resp.json()

        token = data["access_token"]
        expires_in = data.get("expires_in", 7200)
        EbayConnector._class_token_cache[cache_key] = {
            "token": token,
            "expires_at": time.time() + expires_in - 120,
        }
        logger.debug(f"[eBay] Token rafraîchi pour client_id={cache_key[:8]}...")
        return token

    def _auth_headers(self, token: str, marketplace_id: str = "EBAY_FR") -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ── Interface BaseConnector ───────────────────────────────────────────────

    async def validate_connection(self, credentials: Dict[str, Any]) -> bool:
        """Valide les credentials eBay en appelant l'endpoint account."""
        if self._use_mock:
            return True

        required = {"ebay_client_id", "ebay_client_secret", "ebay_refresh_token"}
        if not required.issubset(credentials.keys()):
            logger.warning(f"[eBay] Credentials manquants : {required - credentials.keys()}")
            return False

        try:
            token = await self._get_access_token(credentials)
            marketplace_id = credentials.get("marketplace_id", EBAY_MARKETPLACES["FR"])
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{EBAY_API_BASE}/sell/account/v1/privileges",
                    headers=self._auth_headers(token, marketplace_id),
                )
                resp.raise_for_status()
            logger.info("[eBay] validate_connection : OK")
            return True
        except Exception as exc:
            logger.error(f"[eBay] validate_connection échoué : {exc}")
            return False

    @retry(retries=3, delay=_RATE_LIMIT_DELAY)
    async def fetch_products(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedProduct]:
        """
        Récupère les listings actifs via l'Inventory API eBay.
        Pagine automatiquement sur tous les résultats.
        """
        if self._use_mock or not credentials:
            return self._mock_products(shop_id)

        token = await self._get_access_token(credentials)
        marketplace_id = credentials.get("marketplace_id", EBAY_MARKETPLACES["FR"])
        headers = self._auth_headers(token, marketplace_id)
        products: List[IngestedProduct] = []
        offset = 0
        limit = 200

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                resp = await client.get(
                    f"{EBAY_API_BASE}/sell/inventory/v1/inventory_item",
                    headers=headers,
                    params={"limit": limit, "offset": offset},
                )
                resp.raise_for_status()
                body = resp.json()
                items = body.get("inventoryItems", [])

                for item in items:
                    product_data = item.get("product", {})
                    availability = item.get("availability", {})
                    ship_to_loc = availability.get("shipToLocationAvailability", {})
                    quantity = ship_to_loc.get("quantity", 0)
                    sku = item.get("sku", "")
                    price_obj = item.get("offers", [{}])[0].get("pricingSummary", {}).get("price", {}) if item.get("offers") else {}

                    products.append(
                        IngestedProduct(
                            sku=sku,
                            title=product_data.get("title", "Produit eBay"),
                            description=product_data.get("description", "")[:500] if product_data.get("description") else None,
                            price=float(price_obj.get("value", 0.0)),
                            current_stock=int(quantity),
                            image_url=(product_data.get("imageUrls") or [None])[0],
                            vendor="eBay",
                        )
                    )

                total = body.get("total", 0)
                offset += limit
                if offset >= total or not items:
                    break
                await asyncio.sleep(_RATE_LIMIT_DELAY)

        logger.info(f"[eBay] fetch_products : {len(products)} listings récupérés")
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
        Récupère les ventes journalières via les Orders complétées.
        eBay Analytics API ne supporte pas le filtrage par SKU en v1 →
        on agrège depuis Fulfillment API (Orders filtrées par SKU).
        """
        if self._use_mock or not credentials:
            return self._mock_sales(product_sku, days)

        token = await self._get_access_token(credentials)
        marketplace_id = credentials.get("marketplace_id", EBAY_MARKETPLACES["FR"])
        headers = self._auth_headers(token, marketplace_id)

        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=days)
        sales_by_date: Dict[date, int] = {}
        offset = 0
        limit = 200

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                resp = await client.get(
                    f"{EBAY_API_BASE}/sell/fulfillment/v1/order",
                    headers=headers,
                    params={
                        "filter": (
                            f"creationdate:[{start_dt.strftime('%Y-%m-%dT00:00:00Z')}"
                            f"..{end_dt.strftime('%Y-%m-%dT23:59:59Z')}],"
                            "orderfulfillmentstatus:{FULFILLED}"
                        ),
                        "limit": limit,
                        "offset": offset,
                    },
                )
                resp.raise_for_status()
                body = resp.json()
                orders = body.get("orders", [])

                for order in orders:
                    order_date_str = order.get("creationDate", "")
                    try:
                        order_date = datetime.fromisoformat(
                            order_date_str.replace("Z", "+00:00")
                        ).date()
                    except ValueError:
                        continue

                    for line in order.get("lineItems", []):
                        if line.get("sku") != product_sku:
                            continue
                        qty = int(line.get("quantity", 0))
                        sales_by_date[order_date] = sales_by_date.get(order_date, 0) + qty

                total = body.get("total", 0)
                offset += limit
                if offset >= total or not orders:
                    break
                await asyncio.sleep(_RATE_LIMIT_DELAY)

        sales = [
            IngestedSale(sku=product_sku, date=d, units_sold=qty)
            for d, qty in sorted(sales_by_date.items())
        ]
        logger.info(f"[eBay] fetch_sales_history : {len(sales)} jours pour SKU={product_sku}")
        return sales

    async def fetch_all_data(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Récupère produits + ventes de manière optimisée.
        Utilise le mock si pas de credentials.
        """
        if self._use_mock or not credentials:
            from modules.shopify.infrastructure.mock_generator import generate_full_mock_dataset
            products_raw, sales_raw = generate_full_mock_dataset(count=30, store_id=shop_id)
            return {
                "products": [
                    IngestedProduct(
                        sku=p["sku"], title=p["title"], current_stock=p["current_stock"]
                    )
                    for p in products_raw
                ],
                "sales": [
                    IngestedSale(
                        sku=s.get("sku", ""), date=s["date"],
                        units_sold=int(s["units_sold"]),
                    )
                    for s in sales_raw
                    if s.get("sku")
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
        rng = random.Random(hash(shop_id) % 10000 + 1)

        catalog = [
            ("EB-VET-001", "T-shirt Vintage Coton Bio", "Vêtements", 22.00),
            ("EB-VET-002", "Jean Bootcut Rétro", "Vêtements", 65.00),
            ("EB-BEAU-001", "Palette Aquarelle Makeuo", "Beauté", 28.50),
            ("EB-BEAU-002", "Huile Essentielle Lavande", "Beauté", 12.99),
            ("EB-ACC-001", "Ceinture Cuir Véritable", "Accessoires", 45.00),
            ("EB-ACC-002", "Chapeau Panama Naturel", "Accessoires", 38.00),
            ("EB-BIJ-001", "Collier Vintage Doré", "Bijoux", 29.00),
            ("EB-CHAU-001", "Bottines Western Noires", "Chaussures", 89.00),
        ]

        return [
            IngestedProduct(
                sku=sku,
                title=title,
                description=category,
                price=price,
                current_stock=rng.randint(0, 150),
                vendor="eBay",
            )
            for sku, title, category, price in catalog
        ]

    def _mock_sales(self, product_sku: str, days: int) -> List[IngestedSale]:
        import random
        rng = random.Random(hash(product_sku) + 1)
        today = date.today()
        sales = []

        for i in range(days):
            sale_date = today - timedelta(days=days - 1 - i)
            units = max(0, int(rng.gauss(3, 1.5)))
            sales.append(IngestedSale(sku=product_sku, date=sale_date, units_sold=units))

        return sales
