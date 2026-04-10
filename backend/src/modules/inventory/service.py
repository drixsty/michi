from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger
import uuid

from .models import Product, SalesLog, PlatformSource

class InventoryService:
    """
    Service central pour la gestion des stocks agnostiques Michi.
    Gère l'ingestion, le stockage et la réconciliation des produits.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

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
        s_uuid = uuid.UUID(str(shop_id))
        existing_result = await self.db.execute(
            select(Product).where(Product.shop_id == s_uuid)
        )
        existing_products = {p.sku: p for p in existing_result.scalars().all()}

        # 2. Traiter les produits
        processed_products = []
        for p_data in products_data:
            sku = p_data["sku"]
            if sku in existing_products:
                # UPDATE - Conserver l'ID stable
                p = existing_products[sku]
                p.title = p_data["title"]
                p.current_stock = p_data.get("current_stock", p.current_stock)
                p.source_platform = platform
                p.external_id = p_data.get("external_id")
                processed_products.append(p)
            else:
                # CREATE
                p_data["shop_id"] = s_uuid
                p_data["source_platform"] = platform
                new_p = Product(**p_data)
                self.db.add(new_p)
                processed_products.append(new_p)

        await self.db.flush()
        sku_to_id = {p.sku: p.id for p in processed_products}

        # 3. Gérer les Sales Logs (Remplacer l'historique complet pour chaque produit synchronisé)
        product_ids = [p.id for p in processed_products]
        await self.db.execute(
            delete(SalesLog).where(SalesLog.product_id.in_(product_ids))
        )
        await self.db.flush()

        new_sales_logs = []
        for s_data in sales_data:
            sku = s_data.pop("sku", None)
            if sku and sku in sku_to_id:
                s_data["product_id"] = sku_to_id[sku]
                new_sales_logs.append(SalesLog(**s_data))

        self.db.add_all(new_sales_logs)
        await self.db.flush()

        return {
            "products_count": len(processed_products),
            "sales_logs_count": len(new_sales_logs)
        }

    async def get_products(self, shop_ids: List[str], product_id: str = None) -> List[Product]:
        """
        Lecture unifiée (Agnostique).
        Supporte la recherche multi-boutiques (Organisation) et par ID unique.
        """
        from sqlalchemy.orm import selectinload
        import uuid
        
        # Conversion UUIDs
        s_uuids = [uuid.UUID(str(sid)) for sid in shop_ids]
        p_uuid = uuid.UUID(str(product_id)) if product_id else None
 
        if p_uuid:
            stmt = (
                select(Product)
                .options(
                    selectinload(Product.prediction),
                    selectinload(Product.cleaned_demands),
                    selectinload(Product.supplier),
                    selectinload(Product.sales_logs)
                )
                .where(Product.id == p_uuid)
            )
        else:
            stmt = (
                select(Product)
                .options(
                    selectinload(Product.prediction),
                    selectinload(Product.supplier),
                    selectinload(Product.sales_logs)
                )
                .where(Product.shop_id.in_(s_uuids))
                .order_by(Product.sku)
            )
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_product_settings(
        self, 
        product_id: str, 
        lead_time: Optional[int] = None, 
        moq: Optional[int] = None,
        boost_factor: Optional[float] = None,
        stock_weight: Optional[float] = None,
        cost_price: Optional[float] = None,
        sale_price: Optional[float] = None
    ) -> Product:
        """
        Met à jour les paramètres logistiques d'un produit (Agnostique).
        """
        from sqlalchemy import select
        import uuid
        
        p_uuid = uuid.UUID(str(product_id))
        result = await self.db.execute(
            select(Product).where(Product.id == p_uuid)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise Exception("Produit non trouvé")
            
        if lead_time is not None:
            product.lead_time = lead_time
        if moq is not None:
            product.moq = moq
        if boost_factor is not None:
            product.boost_factor = boost_factor
        if stock_weight is not None:
            product.stock_weight = stock_weight
        if cost_price is not None:
            product.cost_price = cost_price
        if sale_price is not None:
            product.sale_price = sale_price
            
        await self.db.flush()
        
        # Déclenchement du recalcul des prédictions (IA)
        from src.modules.forecasting.service import ForecastingService
        forecasting_service = ForecastingService(self.db)
        await forecasting_service.run_prediction_pipeline(str(product.shop_id))

        return product
