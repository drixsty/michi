from core.database.models import Organization, User, OrganizationMember
"""
InventoryService — Application Layer
Coordinates inventory use cases using domain ports.
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import uuid
from uuid import UUID

from modules.inventory.domain.entities import ProductEntity, SalesLogEntity, PlatformSource
from modules.inventory.domain.ports import IProductRepository, ISalesLogRepository, IStoreRepository

class InventoryService:
    """
    Service central pour la gestion des stocks agnostiques Michi.
    Gère l'ingestion, le stockage et la réconciliation des produits.
    """
    def __init__(
        self, 
        product_repo: IProductRepository, 
        sales_log_repo: ISalesLogRepository,
        store_repo: IStoreRepository
    ):
        self.product_repo = product_repo
        self.sales_log_repo = sales_log_repo
        self.store_repo = store_repo

    async def upsert_inventory_data(
        self, 
        shop_id: str, 
        platform: PlatformSource, 
        products_data: List[Dict[str, Any]], 
        sales_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ingestion unifiée avec UPSERT (Stable UUIDs par SKU).
        Supporte toutes les plateformes (Shopify, CSV, Amazon).
        """
        logger.info(f"[Inventory] UPSERT start for shop {shop_id} (Platform: {platform.value})")

        # 1. Charger les produits existants pour réconciliation
        s_uuid = UUID(str(shop_id))
        existing_products = {p.sku: p for p in await self.product_repo.list_by_store([s_uuid])}

        # 2. Traiter les produits
        processed_entities = []
        for p_data in products_data:
            sku = p_data["sku"]
            if sku in existing_products:
                # UPDATE
                p = existing_products[sku]
                p.title = p_data["title"]
                p.current_stock = p_data.get("current_stock", p.current_stock)
                p.source_platform = platform
                p.external_id = p_data.get("external_id")
                await self.product_repo.save(p)
                processed_entities.append(p)
            else:
                # CREATE
                new_p = ProductEntity(
                    id=uuid.uuid4(),
                    store_id=s_uuid,
                    sku=sku,
                    title=p_data["title"],
                    current_stock=p_data.get("current_stock", 0),
                    source_platform=platform,
                    external_id=p_data.get("external_id")
                )
                saved_p = await self.product_repo.save(new_p)
                processed_entities.append(saved_p)

        sku_to_id = {p.sku: p.id for p in processed_entities}

        # 3. Gérer les Sales Logs
        product_ids = [p.id for p in processed_entities]
        await self.sales_log_repo.delete_by_products(product_ids)

        new_sales_logs = []
        for s_data in sales_data:
            sku = s_data.pop("sku", None)
            if sku and sku in sku_to_id:
                log_entity = SalesLogEntity(
                    id=uuid.uuid4(),
                    product_id=sku_to_id[sku],
                    date=s_data["date"],
                    units_sold=s_data["units_sold"],
                    end_of_day_stock=s_data["end_of_day_stock"]
                )
                new_sales_logs.append(log_entity)

        await self.sales_log_repo.save_batch(new_sales_logs)

        return {
            "products_count": len(processed_entities),
            "sales_logs_count": len(new_sales_logs)
        }

    async def get_products(self, shop_ids: List[str], product_id: str = None) -> List[ProductEntity]:
        """
        Lecture unifiée (Agnostique).
        """
        s_uuids = [UUID(str(sid)) for sid in shop_ids]
        
        # Détecter si product_id est un UUID ou un SKU
        p_uuid = None
        p_sku = None
        if product_id:
            try:
                p_uuid = UUID(str(product_id))
            except ValueError:
                p_sku = str(product_id)
 
        logger.debug(f"[InventoryService] get_products: p_uuid={p_uuid}, p_sku={p_sku}, shop_ids_count={len(s_uuids)}")

        if p_uuid:
            p = await self.product_repo.get_by_id(p_uuid)
            if not p:
                logger.warning(f"[InventoryService] Product ID {p_uuid} not found in repository")
            return [p] if p else []
        elif p_sku:
            items = await self.product_repo.get_by_sku(p_sku, s_uuids)
            logger.debug(f"[InventoryService] Found {len(items)} products for SKU {p_sku} in {len(s_uuids)} stores")
            return items
        else:
            items = await self.product_repo.list_by_store(s_uuids)
            return items

    async def update_product_settings(
        self, 
        product_id: str, 
        **kwargs
    ) -> ProductEntity:
        """
        Met à jour les paramètres logistiques d'un produit (Agnostique).
        """
        try:
            p_uuid = UUID(str(product_id))
        except ValueError:
            raise Exception("UUID invalide pour la mise à jour des paramètres")

        updated_p = await self.product_repo.update_settings(p_uuid, **kwargs)
        if not updated_p:
            raise Exception("Produit non trouvé")
            
        # Note: Recalcul des prédictions sera déclenché par l'orchestrateur ou le resolver
        # pour éviter les dépendances circulaires entre modules au niveau application.
        return updated_p

    async def toggle_source(
        self, 
        org_id: UUID, 
        platform: str, 
        connected: bool, 
        store_id: Optional[UUID] = None
    ) -> Any: # Any to avoid complex StoreEntity imports for now in signature
        """Gère la connexion/déconnexion d'un Store."""
        from modules.inventory.domain.entities import StoreEntity, PlatformSource
        plat_enum = PlatformSource(platform.upper())

        if store_id:
            store = await self.store_repo.get_by_id(store_id)
        else:
            store = await self.store_repo.get_by_platform(org_id, platform)
        
        if not store:
            store = StoreEntity(
                id=uuid.uuid4(),
                organization_id=org_id,
                platform=plat_enum,
                name=platform.capitalize(),
                connected=connected
            )
        else:
            store.name = platform.capitalize()
            store.connected = connected
        
        saved_store = await self.store_repo.save(store)
        
        if not connected:
            logger.warning(f"Disconnecting {platform} for org {org_id}. Deleting associated products.")
            await self.product_repo.delete_by_store(saved_store.id)
            
        return saved_store

    async def ingest_csv_orchestrator(
        self,
        store_id: str,
        csv_content: str,
        mapping: Dict[str, str],
        ingestion_service: Any,
        forecasting_service: Any,
        alert_service: Any
    ) -> Dict[str, Any]:
        """Orchestre l'ingestion CSV complète (Ingestion -> Forecasting -> Alerts)."""
        # 1. Ingestion
        result = await ingestion_service.ingest_from_platform(
            platform="csv",
            shop_id=store_id,
            csv_content=csv_content,
            mapping=mapping
        )
        
        # 2. Forecasting Pipeline
        await forecasting_service.run_cleaning_pipeline(store_id)
        await forecasting_service.run_prediction_pipeline(store_id)
        
        # 3. Alerts
        await alert_service.check_for_stockouts(store_id)
        
        return result
