"""
OmnichannelService — US 9.1 (Sprint 9)

Agrège les stocks par SKU toutes plateformes confondues pour donner
une vue unifiée au marchand multi-canal.

Problème résolu :
    Un marchand vend le SKU "ROBE-NOIR-S" sur Shopify (stock: 12),
    WooCommerce (stock: 8) et Amazon (stock: 5). Sans agrégation,
    il voit 3 lignes séparées et ne connaît pas son stock TOTAL de 25 unités.

Logique d'agrégation :
    GROUP BY (shop_id, sku) → SUM(current_stock), LIST(platforms)

Détection de conflit cross-canal :
    Un conflit est signalé quand le même SKU existe sur 2+ plateformes
    et que le stock TOTAL < run_rate × lead_time (risque de sur-vente).

Performance :
    O(n) — une seule requête SQL avec GROUP BY + agrégation Python.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from .models import Product, PlatformSource
from src.modules.forecasting.models import Prediction


@dataclass
class ChannelStockBreakdown:
    """Stock disponible par canal pour un SKU donné."""
    platform: str        # "shopify", "woocommerce", "amazon", "csv", "custom"
    product_id: str      # UUID du produit dans ce canal
    current_stock: int
    lead_time: int
    moq: int
    run_rate: float
    stock_weight: float


@dataclass
class OmnichannelProduct:
    """
    Vue agrégée d'un SKU sur toutes les plateformes.

    Attributs clés :
        total_stock     : stock total consolidé toutes plateformes
        channel_count   : nombre de canaux sur lesquels ce SKU est présent
        has_conflict    : True si le stock est en tension sur au moins un canal
        dominant_run_rate : run rate le plus élevé (canal qui vend le plus)
    """
    sku: str
    title: str
    total_stock: int
    channels: list[ChannelStockBreakdown] = field(default_factory=list)
    channel_count: int = 0
    has_conflict: bool = False
    predicted_stockout_date: Optional[date] = None
    total_reorder_quantity: int = 0
    dominant_run_rate: float = 0.0


class OmnichannelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_omnichannel_inventory(self, shop_id: str) -> list[OmnichannelProduct]:
        """
        Retourne la vue omnichannel de l'inventaire — agrégation par SKU.

        Charge tous les produits du shop avec leurs prédictions, puis
        agrège par SKU pour donner la vue consolidée.

        Args:
            shop_id: UUID du shop.

        Returns:
            Liste de OmnichannelProduct, triée par total_stock ASC
            (les SKUs les plus à risque en premier).
        """
        # ── 1. Charger tous les produits avec leurs prédictions ──────────────
        result = await self.db.execute(
            select(Product)
            .where(Product.shop_id == shop_id)
            .order_by(Product.sku, Product.source_platform)
        )
        products = list(result.scalars().all())

        if not products:
            return []

        product_ids = [p.id for p in products]

        # ── 2. Charger les prédictions ───────────────────────────────────────
        pred_result = await self.db.execute(
            select(Prediction).where(Prediction.product_id.in_(product_ids))
        )
        predictions = {str(p.product_id): p for p in pred_result.scalars().all()}

        # ── 3. Agréger par SKU ────────────────────────────────────────────────
        sku_map: dict[str, OmnichannelProduct] = {}

        for product in products:
            sku = product.sku
            prediction = predictions.get(str(product.id))

            channel = ChannelStockBreakdown(
                platform=product.source_platform.value,
                product_id=str(product.id),
                current_stock=product.current_stock,
                lead_time=product.lead_time,
                moq=product.moq,
                run_rate=prediction.run_rate if prediction else 0.0,
                stock_weight=product.stock_weight if product.stock_weight is not None else 1.0,
            )

            if sku not in sku_map:
                sku_map[sku] = OmnichannelProduct(
                    sku=sku,
                    title=product.title,
                    total_stock=0,
                    channels=[],
                )

            omni = sku_map[sku]
            omni.channels.append(channel)
            omni.total_stock += product.current_stock
            omni.channel_count = len(omni.channels)

            # Prédictions : on prend la date de rupture la plus proche
            if prediction:
                if (
                    prediction.predicted_stockout_date and (
                        omni.predicted_stockout_date is None
                        or prediction.predicted_stockout_date < omni.predicted_stockout_date
                    )
                ):
                    omni.predicted_stockout_date = prediction.predicted_stockout_date

                # Run rate dominant = le plus élevé (canal le plus actif)
                if prediction.run_rate > omni.dominant_run_rate:
                    omni.dominant_run_rate = prediction.run_rate

                omni.total_reorder_quantity += prediction.reorder_quantity

        # ── 4. Détecter les conflits cross-canal ─────────────────────────────
        for omni in sku_map.values():
            if omni.channel_count > 1:
                # Conflit si run_rate élevé et stock faible sur au moins 1 canal
                for ch in omni.channels:
                    if omni.dominant_run_rate > 0:
                        # Jours de stock sur ce canal
                        days = ch.current_stock / omni.dominant_run_rate
                        if days < ch.lead_time:
                            omni.has_conflict = True
                            break

        # ── 5. Trier par risque (stock faible en premier) ─────────────────────
        result_list = sorted(
            sku_map.values(),
            key=lambda x: (not x.has_conflict, x.total_stock),
        )

        logger.info(
            f"[OmnichannelService] {len(result_list)} SKUs agrégés "
            f"({sum(1 for o in result_list if o.channel_count > 1)} multi-canal)"
        )

        return result_list

    async def get_replenishment_export_data(self, shop_id: str) -> list[dict]:
        """
        Prépare les données d'export CSV pour le plan de réapprovisionnement.

        Retourne une liste de dicts prête pour l'écriture CSV :
            [{ sku, title, platform, current_stock, run_rate, days_of_stock,
               predicted_stockout_date, reorder_quantity, lead_time, moq }]

        Triée par urgence (date de rupture la plus proche en premier).

        Args:
            shop_id: UUID du shop.

        Returns:
            Liste de dicts pour génération CSV.
        """
        result = await self.db.execute(
            select(Product, Prediction)
            .outerjoin(Prediction, Prediction.product_id == Product.id)
            .where(Product.shop_id == shop_id)
            .order_by(Prediction.predicted_stockout_date.asc().nullslast())
        )
        rows = result.all()

        export = []
        for product, prediction in rows:
            export.append({
                "sku": product.sku,
                "title": product.title,
                "platform": product.source_platform.value,
                "current_stock": product.current_stock,
                "run_rate": round(prediction.run_rate, 2) if prediction else 0,
                "days_of_stock": round(prediction.days_of_stock, 1) if prediction and prediction.days_of_stock else None,
                "predicted_stockout_date": str(prediction.predicted_stockout_date) if prediction and prediction.predicted_stockout_date else "N/A",
                "reorder_quantity": prediction.reorder_quantity if prediction else 0,
                "lead_time": product.lead_time,
                "moq": product.moq,
            })

    async def get_channels_for_sku(self, sku: str, shop_id: str) -> list[ChannelStockBreakdown]:
        """
        Retourne la liste des canaux de vente pour un SKU spécifique.
        """
        result = await self.db.execute(
            select(Product)
            .where(Product.shop_id == shop_id, Product.sku == sku)
            .order_by(Product.source_platform)
        )
        products = list(result.scalars().all())

        if not products:
            return []

        product_ids = [p.id for p in products]

        # Charger les prédictions
        pred_result = await self.db.execute(
            select(Prediction).where(Prediction.product_id.in_(product_ids))
        )
        predictions = {str(p.product_id): p for p in pred_result.scalars().all()}

        channels = []
        for product in products:
            prediction = predictions.get(str(product.id))
            channels.append(
                ChannelStockBreakdown(
                    platform=product.source_platform.value,
                    product_id=str(product.id),
                    current_stock=product.current_stock,
                    lead_time=product.lead_time,
                    moq=product.moq,
                    run_rate=prediction.run_rate if prediction else 0.0,
                    stock_weight=product.stock_weight if product.stock_weight is not None else 1.0,
                )
            )

        return channels
