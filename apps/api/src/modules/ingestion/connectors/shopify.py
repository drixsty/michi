"""
Shopify Connector — Michi 道
Intègre l'API Shopify (REST Admin API 2024-01) pour synchroniser produits et ventes.

Authentification : OAuth 2.0 — Access Token (obtenu via /shopify/auth → /shopify/callback)
API utilisées :
  - GET /admin/api/2024-01/products.json   →  fetch_products()
  - GET /admin/api/2024-01/orders.json     →  fetch_sales_history() (fulfilled orders)

Variables requises (StoreCredential.meta) :
  - shopify_domain       : Domaine du shop (ex: ma-boutique.myshopify.com)
  - shopify_access_token : Token Admin API permanent

Mock activé si USE_MOCK_SHOPIFY=true (défaut dev).

Note pagination Shopify : quand page_info est présent, Shopify ignore TOUS les autres
paramètres (status, fields, etc.). On envoie uniquement limit + page_info pour les pages
suivantes afin d'éviter tout comportement indéfini.
"""

import asyncio
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from core.utils import retry
from ..domain.base import BaseConnector
from ..domain.schemas import IngestedProduct, IngestedSale

_SHOPIFY_API_VERSION = "2024-01"
_RATE_LIMIT_DELAY = 0.5
_PAGE_SIZE = 250


class ShopifyConnector(BaseConnector):
    """
    Connecteur Shopify Admin REST API pour Michi.
    Mode mock (USE_MOCK_SHOPIFY=true) ou production.
    """

    def __init__(self):
        self._use_mock: bool = os.getenv("USE_MOCK_SHOPIFY", "true").lower() == "true"

    def _base_url(self, domain: str) -> str:
        return f"https://{domain}/admin/api/{_SHOPIFY_API_VERSION}"

    def _headers(self, access_token: str) -> Dict[str, str]:
        return {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def validate_connection(self, credentials: Dict[str, Any]) -> bool:
        """Valide les credentials Shopify en appelant /shop.json."""
        if self._use_mock:
            return True
        required = {"shopify_domain", "shopify_access_token"}
        if not required.issubset(credentials.keys()):
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self._base_url(credentials['shopify_domain'])}/shop.json",
                    headers=self._headers(credentials["shopify_access_token"]),
                )
                resp.raise_for_status()
            return True
        except Exception as exc:
            logger.error(f"[Shopify] validate_connection échoué : {exc}")
            return False

    @retry(retries=3, delay=_RATE_LIMIT_DELAY)
    async def fetch_products(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedProduct]:
        """Récupère le catalogue Shopify (variantes → un IngestedProduct par SKU)."""
        if self._use_mock or not credentials:
            return self._mock_products(shop_id)

        domain = credentials["shopify_domain"]
        token = credentials["shopify_access_token"]
        products: List[IngestedProduct] = []
        page_info: Optional[str] = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                if page_info:
                    # Shopify ignore tous les autres params quand page_info est présent
                    params: Dict[str, Any] = {"limit": _PAGE_SIZE, "page_info": page_info}
                else:
                    params = {
                        "limit": _PAGE_SIZE,
                        "status": "active",
                        "fields": "id,title,body_html,vendor,variants,images",
                    }

                resp = await client.get(
                    f"{self._base_url(domain)}/products.json",
                    headers=self._headers(token),
                    params=params,
                )
                resp.raise_for_status()
                body = resp.json()

                for product in body.get("products", []):
                    image_url = product["images"][0].get("src") if product.get("images") else None
                    for variant in product.get("variants", []):
                        sku = variant.get("sku") or str(variant.get("id", ""))
                        if not sku:
                            continue
                        products.append(
                            IngestedProduct(
                                sku=sku,
                                title=f"{product['title']} — {variant.get('title', '')}".rstrip(" — "),
                                description=(product.get("body_html") or "")[:500] or None,
                                price=float(variant.get("price", 0)),
                                current_stock=max(0, int(variant.get("inventory_quantity", 0))),
                                image_url=image_url,
                                vendor=product.get("vendor"),
                            )
                        )

                page_info = self._parse_next_page_info(resp.headers.get("Link", ""))
                if not page_info or not body.get("products"):
                    break
                await asyncio.sleep(_RATE_LIMIT_DELAY)

        logger.info(f"[Shopify] fetch_products : {len(products)} variantes")
        return products

    def _parse_next_page_info(self, link_header: str) -> Optional[str]:
        for part in link_header.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
                for param in url.split("?")[-1].split("&"):
                    if param.startswith("page_info="):
                        return param.split("=", 1)[1]
        return None

    @retry(retries=3, delay=_RATE_LIMIT_DELAY)
    async def fetch_sales_history(
        self,
        product_sku: str,
        shop_id: str,  # noqa: ARG002 — conservé pour conformité BaseConnector
        days: int = 365,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedSale]:
        """Récupère les ventes depuis les Orders Shopify filtrées par SKU."""
        if self._use_mock or not credentials:
            return self._mock_sales(product_sku, days)

        domain = credentials["shopify_domain"]
        token = credentials["shopify_access_token"]
        start_dt = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
        sales_by_date: Dict[date, int] = {}
        page_info: Optional[str] = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                if page_info:
                    # Shopify ignore tous les autres params quand page_info est présent
                    params: Dict[str, Any] = {"limit": _PAGE_SIZE, "page_info": page_info}
                else:
                    params = {
                        "limit": _PAGE_SIZE,
                        "status": "any",
                        "fulfillment_status": "fulfilled",
                        "created_at_min": start_dt,
                        "fields": "id,created_at,line_items",
                    }

                resp = await client.get(
                    f"{self._base_url(domain)}/orders.json",
                    headers=self._headers(token),
                    params=params,
                )
                resp.raise_for_status()
                body = resp.json()

                for order in body.get("orders", []):
                    try:
                        order_date = datetime.fromisoformat(
                            order["created_at"].replace("Z", "+00:00")
                        ).date()
                    except (KeyError, ValueError):
                        continue
                    for item in order.get("line_items", []):
                        if item.get("sku") == product_sku:
                            qty = int(item.get("quantity", 0))
                            sales_by_date[order_date] = sales_by_date.get(order_date, 0) + qty

                page_info = self._parse_next_page_info(resp.headers.get("Link", ""))
                if not page_info or not body.get("orders"):
                    break
                await asyncio.sleep(_RATE_LIMIT_DELAY)

        sales = [
            IngestedSale(sku=product_sku, date=d, units_sold=qty)
            for d, qty in sorted(sales_by_date.items())
        ]
        logger.info(f"[Shopify] fetch_sales_history : {len(sales)} jours pour SKU={product_sku}")
        return sales

    async def fetch_all_data(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Récupère produits + ventes (mock ou production)."""
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
                    for s in sales_raw
                    if s.get("sku")
                ],
            }

        products = await self.fetch_products(shop_id, credentials=credentials)
        all_sales: List[IngestedSale] = []
        for product in products:
            all_sales.extend(
                await self.fetch_sales_history(product.sku, shop_id, credentials=credentials)
            )
            await asyncio.sleep(_RATE_LIMIT_DELAY)
        return {"products": products, "sales": all_sales}

    # ── Mock ──────────────────────────────────────────────────────────────────

    def _mock_products(self, shop_id: str) -> List[IngestedProduct]:
        from modules.shopify.infrastructure.mock_generator import generate_mock_products
        raw = generate_mock_products(count=50, store_id=shop_id)
        return [
            IngestedProduct(
                sku=p["sku"], title=p["title"],
                current_stock=p["current_stock"], price=p.get("sale_price", 0.0),
                vendor="Shopify",
            )
            for p in raw
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
