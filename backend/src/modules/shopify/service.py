"""
ShopifyService — Orchestration de la sync mock et lecture produits.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from loguru import logger

from src.modules.inventory.models import Product, SalesLog
from .schemas import SyncResultSchema
from .mock_generator import generate_full_mock_dataset
import random


class ShopifyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_mock_sync(self, shop_id: str) -> SyncResultSchema:
        """
        Synchronisation intelligente (Upsert) :
        Mise à jour des produits existants (par SKU) pour conserver leurs IDs stables.
        Conserve également les réglages utilisateur (Lead Time/MOQ).
        """
        from src.modules.inventory.models import PlatformSource
        logger.info(f"[ShopifyService] Starting smart Upsert sync for shop {shop_id}")

        # 1. Charger les produits existants (indexé par SKU + Plateforme)
        existing_result = await self.db.execute(
            select(Product).where(Product.shop_id == shop_id)
        )
        existing_products = {(p.sku, p.source_platform): p for p in existing_result.scalars().all()}

        # 2. Charger les fournisseurs pour l'assignation
        from src.modules.inventory.models import Supplier
        supplier_result = await self.db.execute(
            select(Supplier).where(Supplier.shop_id == shop_id)
        )
        suppliers = list(supplier_result.scalars().all())

        # 3. Générer le nouveau dataset mock
        products_data, sales_data = generate_full_mock_dataset(count=50, shop_id=shop_id)

        # 3. Traiter les produits (Update ou Create)
        processed_products = []
        for p_data in products_data:
            sku = p_data["sku"]
            platform = p_data.get("source_platform", PlatformSource.SHOPIFY)
            key = (sku, platform)

            if key in existing_products:
                # UPDATE - Conserver l'ID stable
                p = existing_products[key]
                p.title = p_data["title"]
                p.current_stock = p_data["current_stock"]
                # p.source_platform est déjà correct
                # Assigner un fournisseur s'il n'en a pas
                if not p.supplier_id and suppliers:
                    p.supplier_id = random.choice(suppliers).id
                processed_products.append(p)
            else:
                # CREATE
                new_p = Product(**p_data)
                # Assigner un fournisseur aléatoire
                if suppliers:
                    new_p.supplier_id = random.choice(suppliers).id
                self.db.add(new_p)
                processed_products.append(new_p)
        
        await self.db.flush() # Pour avoir les IDs des nouveaux produits
        
        # Mapper les IDs pour les sales logs (par SKU + Plateforme)
        sku_platform_to_id = {(p.sku, p.source_platform): p.id for p in processed_products}

        # 4. Gérer les Sales Logs (Remplacer l'historique complet pour chaque produit synchronisé)
        # On supprime tous les logs existants pour ce shop avant d'insérer les nouveaux
        # (Plus simple que de faire un upsert par date/produit pour ce mock sync)
        product_ids = [p.id for p in processed_products]
        await self.db.execute(
            delete(SalesLog).where(SalesLog.product_id.in_(product_ids))
        )
        await self.db.flush()

        new_sales_logs = []
        for s_data in sales_data:
            # On retrouve le produit via (SKU, Platform)
            sku = s_data.pop("sku", None)
            # On doit passer la plateforme dans s_data ou la déduire?
            # Dans mock_generator.py, on a : 
            # for platform in selected_platforms: products.append(...)
            # all_sales.extend(generate_mock_sales(product["id"], sku=sku, ...))
            # Le product["id"] ici est le UUID temporaire.
            # On peut mapper ce UUID temporaire à l'ID final!
            
        # Re-calculons le mapping TempID -> RealID
        temp_id_to_real_id = {p_data["id"]: p_final.id for p_data, p_final in zip(products_data, processed_products)}

        new_sales_logs = []
        for s_data in sales_data:
            temp_p_id = s_data.pop("product_id", None)
            if temp_p_id in temp_id_to_real_id:
                s_data["product_id"] = temp_id_to_real_id[temp_p_id]
                new_sales_logs.append(SalesLog(**s_data))

        self.db.add_all(new_sales_logs)
        await self.db.flush()

        logger.info(
            f"[ShopifyService] Sync Upsert complete — {len(processed_products)} products, {len(new_sales_logs)} sales logs"
        )

        return SyncResultSchema(
            success=True,
            products_created=len(processed_products),
            sales_logs_created=len(new_sales_logs),
            message=f"Sync intelligente réussie : {len(processed_products)} produits mis à jour/créés.",
        )

    async def update_product_settings(self, shop_id: str, product_id: str, lead_time: int = None, moq: int = None) -> Product:
        """
        Met à jour les paramètres logistiques d'un produit.

        Args:
            shop_id: UUID du shop.
            product_id: UUID du produit.
            lead_time: Nouveau délai de livraison (optionnel).
            moq: Nouvelle quantité min. (optionnel).

        Returns:
            Le produit mis à jour.
        """
        result = await self.db.execute(
            select(Product).where(Product.id == product_id, Product.shop_id == shop_id)
        )
        product = result.scalars().first()
        
        if not product:
            raise Exception("Produit non trouvé")

        if lead_time is not None:
            product.lead_time = lead_time
        if moq is not None:
            product.moq = moq
            
        await self.db.flush()
        return product

    async def get_products(self, shop_id: str, product_id: str = None) -> list[Product]:
        """
        Retourne les produits d'un shop (tous ou un seul filtré par ID).
        Inclut la prédiction associée. Inclut aussi l'historique de demande si product_id est spécifié.
        """
        import uuid
        
        # Conversion UUID explicite pour assurer le matching Postgres
        s_uuid = uuid.UUID(str(shop_id)) if isinstance(shop_id, (str, uuid.UUID)) else shop_id
        p_uuid = uuid.UUID(str(product_id)) if product_id and isinstance(product_id, (str, uuid.UUID)) else product_id
 
        if p_uuid:
            stmt = (
                select(Product)
                .options(
                    selectinload(Product.prediction),
                    selectinload(Product.cleaned_demands),
                    selectinload(Product.supplier),
                    selectinload(Product.sales_logs)
                )
                .where(Product.id == p_uuid, Product.shop_id == s_uuid)
            )
        else:
            stmt = (
                select(Product)
                .options(
                    selectinload(Product.prediction),
                    selectinload(Product.supplier),
                    selectinload(Product.sales_logs)
                )
                .where(Product.shop_id == s_uuid)
                .order_by(Product.sku)
            )
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
