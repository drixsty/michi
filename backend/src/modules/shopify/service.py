"""
ShopifyService — Orchestration de la sync mock spécifique à Shopify.
Les fonctions génériques d'inventaire sont désormais dans InventoryService.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger
import random
import uuid

from src.modules.inventory.models import Product, SalesLog, Supplier, PlatformSource
from .schemas import SyncResultSchema
from .mock_generator import generate_full_mock_dataset


class ShopifyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_mock_sync(self, store_id: str, platform: str = "shopify") -> SyncResultSchema:
        """
        Synchronisation intelligente (Upsert) spécifique à Shopify :
        Régénère un dataset mock et le synchronise via l'inventaire.
        """
        plat_enum = PlatformSource(platform)
        logger.info(f"[ShopifyService] Starting smart mock sync for store {store_id} (Platform: {platform})")

        # 1. Charger les produits existants
        existing_result = await self.db.execute(
            select(Product).where(Product.store_id == store_id)
        )
        existing_products = {(p.sku, p.source_platform): p for p in existing_result.scalars().all()}

        # 2. Charger les fournisseurs
        supplier_result = await self.db.execute(
            select(Supplier).where(Supplier.store_id == store_id)
        )
        suppliers = list(supplier_result.scalars().all())

        # 3. Générer le nouveau dataset mock avec la plateforme forcée
        products_data, sales_data = generate_full_mock_dataset(count=50, store_id=store_id, platform=plat_enum)

        # 4. Traiter les produits (Update ou Create)
        processed_products = []
        for p_data in products_data:
            sku = p_data["sku"]
            platform = p_data.get("source_platform", PlatformSource.SHOPIFY)
            key = (sku, platform)

            if key in existing_products:
                p = existing_products[key]
                p.title = p_data["title"]
                p.current_stock = p_data["current_stock"]
                if not p.supplier_id and suppliers:
                    p.supplier_id = random.choice(suppliers).id
                processed_products.append(p)
            else:
                new_p = Product(**p_data)
                if suppliers:
                    new_p.supplier_id = random.choice(suppliers).id
                self.db.add(new_p)
                processed_products.append(new_p)
        
        await self.db.flush()
        
        # Mapping TempID -> RealID
        temp_id_to_real_id = {p_data["id"]: p_final.id for p_data, p_final in zip(products_data, processed_products)}
        
        logger.info(f"[ShopifyService] {len(processed_products)} products processed. Mapping {len(sales_data)} sales logs...")

        # 5. Gérer les Sales Logs
        product_ids = [p.id for p in processed_products]
        if product_ids:
            await self.db.execute(
                delete(SalesLog).where(SalesLog.product_id.in_(product_ids))
            )
            await self.db.flush()

        new_sales_logs = []
        for s_data in sales_data:
            temp_p_id = s_data.pop("product_id", None)
            if temp_p_id in temp_id_to_real_id:
                real_id = temp_id_to_real_id[temp_p_id]
                if real_id:
                    s_data["product_id"] = real_id
                    new_sales_logs.append(SalesLog(**s_data))

        if new_sales_logs:
            self.db.add_all(new_sales_logs)
            await self.db.flush()
            logger.info(f"[ShopifyService] Successfully inserted {len(new_sales_logs)} sales logs.")

        return SyncResultSchema(
            success=True,
            products_created=len(processed_products),
            sales_logs_created=len(new_sales_logs),
            message=f"Sync mock {platform} réussie : {len(processed_products)} produits.",
        )
