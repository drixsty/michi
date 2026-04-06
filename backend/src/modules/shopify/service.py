"""
ShopifyService — Orchestration de la sync mock et lecture produits.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger

from .models import Product, SalesLog
from .schemas import SyncResultSchema
from .mock_generator import generate_full_mock_dataset


class ShopifyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_mock_sync(self, shop_id: str) -> SyncResultSchema:
        """
        Supprime les données existantes du shop et régénère un dataset mock complet.

        Args:
            shop_id: UUID du shop à synchroniser.

        Returns:
            SyncResultSchema avec le nombre de produits/logs créés.
        """
        logger.info(f"[ShopifyService] Starting mock sync for shop {shop_id}")

        # Supprimer les anciennes données du shop (cascade supprime les sales_logs)
        await self.db.execute(
            delete(Product).where(Product.shop_id == shop_id)
        )
        await self.db.flush()

        # Générer le nouveau dataset
        products_data, sales_data = generate_full_mock_dataset(count=50, shop_id=shop_id)

        # Insérer les produits
        products = [Product(**p) for p in products_data]
        self.db.add_all(products)
        await self.db.flush()

        # Insérer les sales logs en batch
        sales_logs = [SalesLog(**s) for s in sales_data]
        self.db.add_all(sales_logs)
        await self.db.flush()

        logger.info(
            f"[ShopifyService] Sync complete — {len(products)} products, {len(sales_logs)} sales logs"
        )

        return SyncResultSchema(
            success=True,
            products_created=len(products),
            sales_logs_created=len(sales_logs),
            message=f"Sync réussie : {len(products)} produits et {len(sales_logs)} entrées de ventes générés.",
        )

    async def get_products(self, shop_id: str) -> list[Product]:
        """
        Retourne tous les produits d'un shop triés par SKU.

        Args:
            shop_id: UUID du shop.

        Returns:
            Liste de modèles Product.
        """
        result = await self.db.execute(
            select(Product)
            .where(Product.shop_id == shop_id)
            .order_by(Product.sku)
        )
        return list(result.scalars().all())
