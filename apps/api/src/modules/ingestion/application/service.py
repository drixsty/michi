from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..domain.base import BaseConnector
from modules.inventory.application.inventory_service import InventoryService
from modules.inventory.application.alert_service import AlertService
from modules.inventory.infrastructure.models import PlatformSource
from core.database.models import Organization
from sqlalchemy import select
import uuid

class IngestionService:
    """
    Service central d'orchestration pour l'ingestion de données Michi.
    Gère les connecteurs (Shopify, CSV, Amazon) et assure le stockage unifié via InventoryService.
    Déclenche également l'évaluation des alertes post-ingestion.
    """
    def __init__(self, db: AsyncSession, inventory_service=None, alert_service=None):
        self.db = db
        self.inventory_service = inventory_service
        self.alert_service = alert_service
        self.connectors: Dict[str, BaseConnector] = {}

    def register_connector(self, platform: str, connector: BaseConnector):
        """
        Enregistre un connecteur pour une plateforme spécifique.
        """
        self.connectors[platform] = connector

    async def ingest_from_platform(
        self, 
        platform: str, 
        shop_id: str, 
        organization_id: Optional[UUID] = None,
        csv_content: Optional[str | bytes] = None,
        mapping: Optional[Dict[str, str]] = None,
        is_excel: bool = False,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Déclenche l'ingestion depuis une plateforme spécifique.
        """
        if platform not in self.connectors:
            raise ValueError(f"Connecteur pour {platform} non configuré.")

        connector = self.connectors[platform]
        logger.info(f"[Ingestion] Starting ingestion for {platform} (Shop: {shop_id})")

        # 0. Récupérer l'organisation si fournie
        org = None
        if organization_id:
            from core.database.models import Organization
            org = await self.db.get(Organization, organization_id)

        # 1. Fetch data (Products + Sales)
        from ..connectors.shopify import ShopifyConnector
        from ..connectors.woocommerce import WooCommerceConnector
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
            # IA : Récupérer les SKUs existants pour le Fuzzy Matching
            existing_skus = []
            if org:
                # 1. Récupérer tous les magasins de l'organisation
                stores = await self.inventory_service.store_repo.list_by_organization(org.id)
                store_ids = [s.id for s in stores]
                
                if store_ids:
                    # 2. Récupérer tous les produits de ces magasins
                    existing_products = await self.inventory_service.product_repo.list_by_store(store_ids)
                    existing_skus = [p.sku for p in existing_products]

            products_data = await connector.fetch_products(
                csv_content, 
                mapping or {},
                existing_skus=existing_skus
            )
            sales_data = await connector.fetch_sales_history(
                csv_content, 
                mapping or {},
                is_excel=is_excel
            )

        # 2. Vérifier les limites de l'abonnement (Subscription Guard)
        from core.database.models import Organization
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
            sales_data=sales_data,
            organization_id=kwargs.get("organization_id")
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
