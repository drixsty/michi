"""
Etsy Connector — Michi 道
Intègre l'Etsy Open API v3 pour synchroniser produits et commandes.

Authentification : OAuth 2.0 PKCE — Authorization Code + Refresh Token
API utilisées :
  - GET /v3/application/shops/{shop_id}/listings/active   →  fetch_products()
  - GET /v3/application/shops/{shop_id}/receipts          →  fetch_sales_history()
  - GET /v3/application/listings/{listing_id}/inventory   →  stock par variante

Scopes OAuth requis (Etsy v3) :
  - listings_r       : Lecture des listings
  - transactions_r   : Lecture des commandes (receipts)
  - shops_r          : Lecture profil shop

Variables d'environnement requises (StoreCredential.meta) :
  - etsy_client_id      : Keystring de l'app Etsy
  - etsy_access_token   : Access Token OAuth
  - etsy_refresh_token  : Refresh Token
  - etsy_shop_id        : Shop ID numérique Etsy du vendeur

Mock activé si settings.USE_MOCK_ETSY = True (défaut dev).

Particularités Etsy :
  - Listings = produits avec variantes (taille, couleur)
  - Receipts = commandes consolidées (≠ line items individuels)
  - Rate limit : 10 req/s, quota journalier 5 000 req/clé
  - Refresh token valide 90 jours (à renouveler côté UI)
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

# ── Constantes Etsy API ───────────────────────────────────────────────────────

ETSY_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
ETSY_API_BASE = "https://openapi.etsy.com/v3"

_RATE_LIMIT_DELAY = 0.12  # ~8 req/s (marge sous le quota de 10/s)
_RECEIPT_PAGE_LIMIT = 100  # max par page pour l'API receipts


class EtsyConnector(BaseConnector):
    """
    Connecteur Etsy Open API v3 pour Michi.
    Spécialité : gestion des variantes (taille/couleur → SKU composite).

    Cache token partagé au niveau classe pour éviter les refreshes inutiles
    causés par ConnectorFactory (nouvelle instance à chaque appel).
    """

    # Cache partagé entre toutes les instances (clé = etsy_client_id)
    _class_token_cache: Dict[str, Any] = {}

    def __init__(self):
        self._use_mock: bool = os.getenv("USE_MOCK_ETSY", "true").lower() == "true"

    # ── Authentification OAuth ────────────────────────────────────────────────

    async def _get_access_token(self, credentials: Dict[str, Any]) -> str:
        """
        Rafraîchit le token Etsy si expiré (TTL 3600s, cache 55 min).
        Si etsy_access_token est fourni directement, l'utilise tel quel.
        """
        cache_key = credentials.get("etsy_client_id", "")
        cached = EtsyConnector._class_token_cache.get(cache_key)

        if cached and cached["expires_at"] > time.time():
            return cached["token"]

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                ETSY_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": credentials["etsy_client_id"],
                    "refresh_token": credentials["etsy_refresh_token"],
                },
            )
            resp.raise_for_status()
            data = resp.json()

        token = data["access_token"]
        EtsyConnector._class_token_cache[cache_key] = {
            "token": token,
            "expires_at": time.time() + data.get("expires_in", 3600) - 300,
        }
        logger.debug(f"[Etsy] Token rafraîchi pour client_id={cache_key[:8]}...")
        return token

    def _auth_headers(self, token: str, client_id: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "x-api-key": client_id,
            "Accept": "application/json",
        }

    # ── Interface BaseConnector ───────────────────────────────────────────────

    async def validate_connection(self, credentials: Dict[str, Any]) -> bool:
        """Valide les credentials Etsy en lisant le profil du shop."""
        if self._use_mock:
            return True

        required = {"etsy_client_id", "etsy_shop_id"}
        if not required.issubset(credentials.keys()):
            logger.warning(f"[Etsy] Credentials manquants : {required - credentials.keys()}")
            return False
        if not credentials.get("etsy_refresh_token") and not credentials.get("etsy_access_token"):
            logger.warning("[Etsy] etsy_refresh_token ou etsy_access_token requis")
            return False

        try:
            token = await self._get_access_token(credentials)
            shop_id = credentials["etsy_shop_id"]
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{ETSY_API_BASE}/application/shops/{shop_id}",
                    headers=self._auth_headers(token, credentials["etsy_client_id"]),
                )
                resp.raise_for_status()
            logger.info("[Etsy] validate_connection : OK")
            return True
        except Exception as exc:
            logger.error(f"[Etsy] validate_connection échoué : {exc}")
            return False

    @retry(retries=3, delay=_RATE_LIMIT_DELAY)
    async def fetch_products(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedProduct]:
        """
        Récupère les listings actifs depuis l'API Etsy.
        Chaque listing peut avoir des variantes → un IngestedProduct par SKU de variante.
        Si pas de variantes, le listing_id sert de SKU.
        """
        if self._use_mock or not credentials:
            return self._mock_products(shop_id)

        token = await self._get_access_token(credentials)
        etsy_shop_id = credentials.get("etsy_shop_id", shop_id)
        client_id = credentials["etsy_client_id"]
        headers = self._auth_headers(token, client_id)
        products: List[IngestedProduct] = []
        offset = 0
        limit = 100

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                resp = await client.get(
                    f"{ETSY_API_BASE}/application/shops/{etsy_shop_id}/listings/active",
                    headers=headers,
                    params={
                        "limit": limit,
                        "offset": offset,
                        "includes": ["Images", "Inventory"],
                    },
                )
                resp.raise_for_status()
                body = resp.json()
                listings = body.get("results", [])

                for listing in listings:
                    listing_id = str(listing.get("listing_id", ""))
                    title = listing.get("title", "Produit Etsy")
                    description = (listing.get("description") or "")[:500]
                    price = listing.get("price", {}).get("amount", 0) / listing.get("price", {}).get("divisor", 100)
                    image_url = None
                    if listing.get("images"):
                        image_url = listing["images"][0].get("url_fullxfull")

                    inventory = listing.get("inventory", {})
                    products_data = inventory.get("products", [])

                    if products_data:
                        # Variantes → un IngestedProduct par variante avec SKU composite
                        for variant in products_data:
                            offerings = variant.get("offerings", [{}])
                            active_offering = next(
                                (o for o in offerings if o.get("is_enabled")), offerings[0] if offerings else {}
                            )
                            sku = variant.get("sku") or f"{listing_id}-{variant.get('product_id', '')}"
                            variant_price = active_offering.get("price", {}).get("amount", 0) / active_offering.get("price", {}).get("divisor", 100) if active_offering.get("price") else price
                            quantity = active_offering.get("quantity", 0)

                            products.append(
                                IngestedProduct(
                                    sku=sku or listing_id,
                                    title=f"{title} — {self._variant_label(variant)}",
                                    description=description or None,
                                    price=float(variant_price),
                                    current_stock=int(quantity),
                                    image_url=image_url,
                                    vendor="Etsy",
                                )
                            )
                    else:
                        # Listing sans variante
                        products.append(
                            IngestedProduct(
                                sku=listing_id,
                                title=title,
                                description=description or None,
                                price=float(price),
                                current_stock=int(listing.get("quantity", 0)),
                                image_url=image_url,
                                vendor="Etsy",
                            )
                        )

                count = body.get("count", 0)
                offset += limit
                if offset >= count or not listings:
                    break
                await asyncio.sleep(_RATE_LIMIT_DELAY)

        logger.info(f"[Etsy] fetch_products : {len(products)} produits/variantes récupérés")
        return products

    def _variant_label(self, variant: Dict[str, Any]) -> str:
        """Construit un label lisible depuis les property_values du variant."""
        props = variant.get("property_values", [])
        if not props:
            return ""
        parts = []
        for prop in props:
            values = prop.get("values", [])
            if values:
                parts.append(str(values[0]))
        return " / ".join(parts)

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
        Récupère les ventes depuis les Receipts Etsy (commandes finalisées).
        Agrège par SKU + date.

        Note : was_shipped=true exclut les produits digitaux et les commandes
        en attente d'expédition. On filtre uniquement sur was_paid=true.
        """
        if self._use_mock or not credentials:
            return self._mock_sales(product_sku, days)

        token = await self._get_access_token(credentials)
        etsy_shop_id = credentials.get("etsy_shop_id", shop_id)
        client_id = credentials["etsy_client_id"]
        headers = self._auth_headers(token, client_id)

        min_created = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        sales_by_date: Dict[date, int] = {}
        offset = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                resp = await client.get(
                    f"{ETSY_API_BASE}/application/shops/{etsy_shop_id}/receipts",
                    headers=headers,
                    params={
                        "limit": _RECEIPT_PAGE_LIMIT,
                        "offset": offset,
                        "min_created": min_created,
                        "was_paid": "true",
                        "includes": ["Transactions"],
                    },
                )
                resp.raise_for_status()
                body = resp.json()
                receipts = body.get("results", [])

                for receipt in receipts:
                    created_ts = receipt.get("create_timestamp", 0)
                    sale_date = date.fromtimestamp(created_ts)

                    for transaction in receipt.get("transactions", []):
                        # Priorité 1 : SKU explicite sur la transaction (vendeur l'a configuré)
                        tx_sku = transaction.get("sku") or ""

                        # Priorité 2 : SKU dans product_data (ListingProduct object)
                        if not tx_sku:
                            product_data = transaction.get("product_data", {})
                            if product_data:
                                tx_sku = product_data.get("sku") or ""

                        # Priorité 3 : clé composite listing_id-product_id (sans SKU explicite)
                        if not tx_sku:
                            listing_id = str(transaction.get("listing_id", ""))
                            product_id = str(transaction.get("product_id", ""))
                            tx_sku = f"{listing_id}-{product_id}" if product_id else listing_id

                        if tx_sku != product_sku:
                            continue

                        qty = int(transaction.get("quantity", 0))
                        sales_by_date[sale_date] = sales_by_date.get(sale_date, 0) + qty

                count = body.get("count", 0)
                offset += _RECEIPT_PAGE_LIMIT
                if offset >= count or not receipts:
                    break
                await asyncio.sleep(_RATE_LIMIT_DELAY)

        sales = [
            IngestedSale(sku=product_sku, date=d, units_sold=qty)
            for d, qty in sorted(sales_by_date.items())
        ]
        logger.info(f"[Etsy] fetch_sales_history : {len(sales)} jours pour SKU={product_sku}")
        return sales

    async def fetch_all_data(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Récupère produits + ventes de manière optimisée.
        """
        if self._use_mock or not credentials:
            from modules.shopify.infrastructure.mock_generator import generate_full_mock_dataset
            products_raw, sales_raw = generate_full_mock_dataset(count=20, store_id=shop_id)
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
        rng = random.Random(hash(shop_id) % 10000 + 2)

        catalog = [
            ("ETY-001", "Robe Bohème Fleuri Fait Main", "Vêtements", 78.00),
            ("ETY-002", "Collier Macramé Artisanal", "Bijoux", 32.00),
            ("ETY-003", "Bougie Soja Parfumée Lavande", "Maison", 18.50),
            ("ETY-004", "Sac Crochet Été Naturel", "Accessoires", 45.00),
            ("ETY-005", "Carnet Couverture Cuir Vintage", "Papeterie", 22.00),
            ("ETY-006", "Earrings Céramique Colorée", "Bijoux", 24.00),
            ("ETY-007", "Print Affiche Aquarelle A3", "Décoration", 15.00),
            ("ETY-008", "Chapeau Soleil Paille Coloré", "Accessoires", 35.00),
        ]

        return [
            IngestedProduct(
                sku=sku,
                title=title,
                description=category,
                price=price,
                current_stock=rng.randint(0, 50),
                vendor="Etsy",
            )
            for sku, title, category, price in catalog
        ]

    def _mock_sales(self, product_sku: str, days: int) -> List[IngestedSale]:
        import random
        rng = random.Random(hash(product_sku) + 2)
        today = date.today()
        sales = []

        for i in range(days):
            sale_date = today - timedelta(days=days - 1 - i)
            # Etsy : volume de vente plus faible, artisanat
            units = max(0, int(rng.gauss(1.5, 1.0)))
            sales.append(IngestedSale(sku=product_sku, date=sale_date, units_sold=units))

        return sales
