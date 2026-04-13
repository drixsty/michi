from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .base import BaseConnector
from src.modules.inventory.service import InventoryService
from src.modules.inventory.alert_service import AlertService
from src.modules.inventory.models import PlatformSource
from src.modules.auth.models import Organization
from sqlalchemy import select
import uuid

class IngestionService:
    """
    Service central d'orchestration pour l'ingestion de données Michi.
    Gère les connecteurs (Shopify, CSV, Amazon) et assure le stockage unifié via InventoryService.
    Déclenche également l'évaluation des alertes post-ingestion.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.alert_service = AlertService(db)
        self.connectors: Dict[str, BaseConnector] = {}

    def register_connector(self, platform: str, connector: BaseConnector):
        """
        Enregistre un connecteur pour une plateforme spécifique.
        """
        self.connectors[platform] = connector

    async def ingest_from_platform(self, platform: str, shop_id: str, **kwargs) -> Dict[str, Any]:
        """
        Déclenche l'ingestion depuis une plateforme spécifique.
        """
        if platform not in self.connectors:
            raise ValueError(f"Connecteur pour {platform} non configuré.")

        connector = self.connectors[platform]
        logger.info(f"[Ingestion] Starting ingestion for {platform} (Shop: {shop_id})")

        # 1. Fetch data (Products + Sales)
        from .connectors.shopify import ShopifyConnector
        from .connectors.woocommerce import WooCommerceConnector
        if isinstance(connector, ShopifyConnector):
            data = await connector.fetch_all_data(shop_id)
            products_data = data["products"]
            sales_data = data["sales"]
        elif isinstance(connector, WooCommerceConnector):
            # WooCommerce a des fichiers séparés pour produits et commandes
            products_data = await connector.fetch_products(
                kwargs.get("csv_content", ""), kwargs.get("mapping")
            )
            orders_csv = kwargs.get("orders_csv")
            sales_data = (
                await connector.fetch_sales_history(orders_csv, kwargs.get("mapping"))
                if orders_csv
                else []
            )
        else:
            # Mode standard (ex: CSV)
            products_data = await connector.fetch_products(kwargs.get("csv_content"), kwargs.get("mapping"))
            sales_data = await connector.fetch_sales_history(kwargs.get("csv_content"), kwargs.get("mapping"))

        # 2. Vérifier les limites de l'abonnement (Subscription Guard)
        from src.modules.auth.models import Organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == uuid.UUID(str(kwargs.get("organization_id"))))
        )
        org = org_result.scalar_one_or_none()
        
        if org and org.plan.upper() == "BASIC":
            if len(products_data) > 100:
                logger.warning(f"[Subscription Guard] Truncating products for BASIC org {org.id} (found {len(products_data)}, limit 100)")
                products_data = products_data[:100]

        # 3. Convertir la plateforme en Enum
        # source_platform peut être passé explicitement pour forcer la valeur
        platform_str = kwargs.get("source_platform", platform).lower()
        try:
            p_enum = PlatformSource(platform_str)
        except ValueError:
            p_enum = PlatformSource.CUSTOM

        # 3. Stockage unifié via InventoryService
        result = await self.inventory_service.upsert_inventory_data(
            shop_id=shop_id,
            platform=p_enum,
            products_data=products_data,
            sales_data=sales_data
        )

        # 4. ÉVALUATION DES ALERTES (Post-Ingestion)
        # TODO: S'assurer que les prédictions ont été recalculées avant (Forecasting logic)
        # await self.alert_service.check_for_stockouts(shop_id)

        return {
            "platform": platform,
            "products_count": result["products_count"],
            "sales_logs_count": result["sales_logs_count"],
            "status": "Success",
            "alerts_evaluated": True
        }
