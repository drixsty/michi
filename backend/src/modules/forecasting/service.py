"""
ForecastingService — Pipeline de nettoyage de la demande.

Pipeline :
    1. Lecture des sales_logs du shop (SQLAlchemy → Pandas)
    2. Out-of-Stock Correction (moyenne mobile 14j)
    3. Outlier Detection & Correction (IQR)
    4. Écriture dans cleaned_demand (upsert par product_id + date)
"""
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger

from src.modules.shopify.models import Product, SalesLog
from .models import CleanedDemand
from .schemas import PipelineResultSchema, CleanedDemandSchema
from .algorithms.out_of_stock_correction import correct_out_of_stock_batch
from .algorithms.outlier_detection import detect_outliers_batch


class ForecastingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_cleaning_pipeline(self, shop_id: str) -> PipelineResultSchema:
        """
        Exécute la pipeline complète OOS + IQR pour tous les produits du shop.

        Args:
            shop_id: UUID du shop.

        Returns:
            PipelineResultSchema avec les statistiques de nettoyage.
        """
        logger.info(f"[ForecastingService] Pipeline start — shop {shop_id}")

        # ── 1. Charger les produits du shop ───────────────────────────────────
        products_result = await self.db.execute(
            select(Product).where(Product.shop_id == shop_id)
        )
        products = list(products_result.scalars().all())

        if not products:
            return PipelineResultSchema(
                success=False,
                products_processed=0,
                rows_written=0,
                stockout_corrections=0,
                outlier_corrections=0,
                message="Aucun produit trouvé. Lancez d'abord une synchronisation.",
            )

        product_ids = [p.id for p in products]

        # ── 2. Charger les sales_logs ─────────────────────────────────────────
        logs_result = await self.db.execute(
            select(SalesLog)
            .where(SalesLog.product_id.in_(product_ids))
            .order_by(SalesLog.product_id, SalesLog.date)
        )
        logs = logs_result.scalars().all()

        if not logs:
            return PipelineResultSchema(
                success=False,
                products_processed=0,
                rows_written=0,
                stockout_corrections=0,
                outlier_corrections=0,
                message="Aucun historique de ventes trouvé.",
            )

        # ── 3. Construire le DataFrame ────────────────────────────────────────
        df = pd.DataFrame([{
            "product_id": str(log.product_id),
            "date": log.date,
            "units_sold": float(log.units_sold),
            "end_of_day_stock": int(log.end_of_day_stock),
        } for log in logs])

        # ── 4. OOS Correction ─────────────────────────────────────────────────
        df = correct_out_of_stock_batch(df)

        # ── 5. Outlier Detection ──────────────────────────────────────────────
        df = detect_outliers_batch(df)

        # ── 6. Déterminer correction_type ─────────────────────────────────────
        def _correction_type(row) -> str:
            if row["is_stockout"] and row["is_outlier"]:
                return "stockout+outlier"
            if row["is_stockout"]:
                return "stockout"
            if row["is_outlier"]:
                return "outlier"
            return "none"

        df["correction_type"] = df.apply(_correction_type, axis=1)

        # corrected_units_sold = résultat final après les deux passes
        # - Si jour de rupture → theoretical_units_sold (OOS corrigé)
        # - Ensuite IQR corrige les outliers → corrected_units_sold
        # corrected_units_sold contient déjà la valeur finale (IQR travaille sur theoretical)

        # ── 7. Supprimer l'ancienne cleaned_demand du shop ────────────────────
        await self.db.execute(
            delete(CleanedDemand).where(CleanedDemand.product_id.in_(product_ids))
        )
        await self.db.flush()

        # ── 8. Insérer les nouvelles lignes ───────────────────────────────────
        rows = []
        for _, row in df.iterrows():
            rows.append(CleanedDemand(
                product_id=row["product_id"],
                date=row["date"],
                raw_units_sold=float(row["units_sold"]),
                corrected_units_sold=float(row["corrected_units_sold"]),
                is_stockout=bool(row["is_stockout"]),
                is_outlier=bool(row["is_outlier"]),
                correction_type=str(row["correction_type"]),
            ))

        self.db.add_all(rows)
        await self.db.flush()

        # ── Statistiques ──────────────────────────────────────────────────────
        stockout_corrections = int(df["is_stockout"].sum())
        outlier_corrections = int(df["is_outlier"].sum())

        logger.info(
            f"[ForecastingService] Done — {len(products)} products, "
            f"{len(rows)} rows, {stockout_corrections} OOS, {outlier_corrections} outliers"
        )

        return PipelineResultSchema(
            success=True,
            products_processed=len(products),
            rows_written=len(rows),
            stockout_corrections=stockout_corrections,
            outlier_corrections=outlier_corrections,
            message=(
                f"Pipeline terminée : {len(products)} produits traités, "
                f"{stockout_corrections} corrections OOS, "
                f"{outlier_corrections} outliers corrigés."
            ),
        )

    async def get_cleaned_demand(
        self, product_id: str, limit: int = 365
    ) -> list[CleanedDemand]:
        """
        Retourne la demande nettoyée pour un produit, triée par date décroissante.

        Args:
            product_id: UUID du produit.
            limit: Nombre maximum d'entrées (défaut: 365).

        Returns:
            Liste de CleanedDemand.
        """
        result = await self.db.execute(
            select(CleanedDemand)
            .where(CleanedDemand.product_id == product_id)
            .order_by(CleanedDemand.date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
