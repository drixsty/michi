from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from uuid import UUID

from ..domain.base import BaseConnector
from modules.inventory.infrastructure.models import PlatformSource


class IngestionService:
    """
    Service central d'orchestration pour l'ingestion de données Michi.
    Gère les connecteurs (Shopify, CSV, Amazon, eBay, Etsy, WooCommerce)
    et assure le stockage unifié via InventoryService.
    """

    def __init__(self, db: AsyncSession, inventory_service=None, alert_service=None):
        self.db = db
        self.inventory_service = inventory_service
        self.alert_service = alert_service
        self.connectors: Dict[str, BaseConnector] = {}

    def register_connector(self, platform: str, connector: BaseConnector):
        """Enregistre un connecteur pour une plateforme spécifique."""
        self.connectors[platform] = connector

    async def ingest_from_platform(
        self,
        platform: str,
        shop_id: str,
        organization_id: Optional[UUID] = None,
        csv_content: Optional[str | bytes] = None,
        mapping: Optional[Dict[str, str]] = None,
        is_excel: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Déclenche l'ingestion depuis une plateforme spécifique.

        Args:
            platform        : Clé plateforme (SHOPIFY, AMAZON, EBAY, ETSY, WOOCOMMERCE, CSV).
            shop_id         : UUID du store Michi.
            organization_id : UUID de l'organisation (pour le Subscription Guard).
            csv_content     : Contenu brut du fichier (CSV/WooCommerce uniquement).
            mapping         : Mapping colonnes CSV → champs Michi.
            is_excel        : True si le fichier est un .xlsx.
            **kwargs        :
                credentials  : Dict secrets déchiffrés du StoreCredential (API connectors).
                orders_csv   : CSV commandes WooCommerce séparé.
                source_platform : Override de la plateforme pour le stockage.
        """
        if platform not in self.connectors:
            raise ValueError(f"Connecteur pour '{platform}' non configuré.")

        connector = self.connectors[platform]
        logger.info(f"[Ingestion] Démarrage ingestion {platform} (Shop: {shop_id})")

        # Récupérer l'organisation pour le Subscription Guard
        org = None
        if organization_id:
            from core.database.models import Organization
            org = await self.db.get(Organization, organization_id)

        # ── 1. Fetch data selon le type de connecteur ─────────────────────────
        from ..connectors.shopify import ShopifyConnector
        from ..connectors.woocommerce import WooCommerceConnector
        from ..connectors.amazon import AmazonConnector
        from ..connectors.ebay import EbayConnector
        from ..connectors.etsy import EtsyConnector
        from ..connectors.csv import CSVConnector

        credentials: Optional[Dict[str, Any]] = kwargs.get("credentials")

        if isinstance(connector, (ShopifyConnector, AmazonConnector, EbayConnector, EtsyConnector)):
            # Connecteurs API — passent credentials pour l'authentification OAuth/LWA
            data = await connector.fetch_all_data(shop_id, credentials=credentials)
            products_data = data["products"]
            sales_data = data["sales"]

        elif isinstance(connector, WooCommerceConnector):
            # WooCommerce : deux fichiers CSV distincts (produits / commandes)
            woo_raw = kwargs.get("csv_content") or csv_content or ""
            woo_content: str = woo_raw if isinstance(woo_raw, str) else woo_raw.decode("utf-8", errors="replace")
            products_data = await connector.fetch_products(
                woo_content, kwargs.get("mapping")
            )
            orders_csv: Optional[str] = kwargs.get("orders_csv")
            sales_data = (
                await connector.fetch_sales_history(orders_csv, kwargs.get("mapping"))
                if orders_csv
                else []
            )

        else:
            # Mode CSV universel — fuzzy matching IA sur SKUs existants
            existing_skus: list[str] = []
            if org and self.inventory_service is not None:
                stores = await self.inventory_service.store_repo.list_by_organization(org.id)
                store_ids = [s.id for s in stores]
                if store_ids:
                    existing_products = await self.inventory_service.product_repo.list_by_store(store_ids)
                    existing_skus = [p.sku for p in existing_products]

            products_data = await connector.fetch_products(  # type: ignore[arg-type]
                csv_content,
                mapping or {},
                existing_skus=existing_skus,
            )
            sales_data = await connector.fetch_sales_history(  # type: ignore[arg-type]
                csv_content,
                mapping or {},
                is_excel=is_excel,
            )

        # ── 2. Subscription Guard ─────────────────────────────────────────────
        if org and org.plan.upper() == "BASIC" and len(products_data) > 100:
            logger.warning(
                f"[Subscription Guard] Truncating for BASIC org {org.id} "
                f"({len(products_data)} → 100 produits)"
            )
            products_data = products_data[:100]

        # ── 3. Résolution PlatformSource ──────────────────────────────────────
        platform_key = kwargs.get("source_platform", platform).upper()
        try:
            p_enum = PlatformSource(platform_key)
        except ValueError:
            p_enum = PlatformSource.CUSTOM

        # ── 4. Persistance via InventoryService ───────────────────────────────
        if self.inventory_service is None:
            logger.warning("[Ingestion] inventory_service non configuré — données non persistées")
            return {
                "platform": platform,
                "products_count": len(products_data),
                "sales_logs_count": len(sales_data),
                "status": "DryRun",
                "alerts_evaluated": False,
            }

        result = await self.inventory_service.upsert_inventory_data(
            shop_id=shop_id,
            platform=p_enum,
            products_data=products_data,
            sales_data=sales_data,
            organization_id=kwargs.get("organization_id"),
        )

        logger.info(
            f"[Ingestion] {platform} terminé — "
            f"{result['products_count']} produits, {result['sales_logs_count']} ventes"
        )

        return {
            "platform": platform,
            "products_count": result["products_count"],
            "sales_logs_count": result["sales_logs_count"],
            "status": "Success",
            "alerts_evaluated": True,
        }
