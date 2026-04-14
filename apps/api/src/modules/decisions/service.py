from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.modules.inventory.models import Product, PlatformSource, Store
from src.modules.forecasting.models import Prediction
from src.modules.auth.models import User
from loguru import logger
from .schemas import FinancialKpiSchema, DecisionCenterOverview
from src.modules.intelligence.analytics import (
    calculate_financial_kpis,
    calculate_health_score,
    score_products,
)

class DecisionCenterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, user_id: str, store_id: Optional[str] = None, channel: Optional[str] = None) -> DecisionCenterOverview:
        user_res = await self.db.execute(select(User).where(User.id == user_id))
        user = user_res.scalars().first()
        if not user:
            raise Exception("Utilisateur non trouvé")

        prefs = user.preferences or {}
        is_mutualized = prefs.get("is_mutualized", False)
        currency = prefs.get("currency", "€")

        if not user.current_organization_id:
            return DecisionCenterOverview(
                kpis=FinancialKpiSchema(inventory_value_cost=0, inventory_value_sale=0, revenue_at_risk=0, stock_coverage_avg_days=0, currency=currency, is_mutualized=is_mutualized),
                top_risks=[], active_platforms=[], capital_breakdown=[], total_run_rate=0.0, total_stock=0, health_score=0, message="Pas d'organisation."
            )

        # 1. Toutes les sources connectées
        all_stores_res = await self.db.execute(select(Store).where(Store.organization_id == user.current_organization_id, Store.connected == True))
        all_stores = all_stores_res.scalars().all()
        all_platforms = sorted(list(set(s.platform.value.upper() for s in all_stores)))
        
        # 2. Stores filtrés pour le calcul (Agrégation par organisation)
        # On ignore délibérément store_id car une organisation correspond à une boutique unifiée
        active_store_ids = [s.id for s in all_stores]
        
        # 3. Query
        product_filter = Product.store_id.in_(active_store_ids)
        if channel and channel.lower() != 'all':
            print(f"[DecisionCenter] Filtering by sub-channel: {channel}")
            try:
                target_platform = PlatformSource(channel.upper())
                product_filter = and_(product_filter, Product.source_platform == target_platform)
            except (ValueError, KeyError):
                logger.warning(f"Invalid channel requested: {channel}")

        stmt = (
            select(Product, Prediction)
            .outerjoin(Prediction, Product.id == Prediction.product_id)
            .where(product_filter)
        )
        res = await self.db.execute(stmt)
        data = res.all()
        print(f"[DEBUG] Decisions for channel {channel}: found {len(data)} rows")
        if len(data) > 0:
            print(f"[DEBUG] First row platform: {data[0][0].source_platform}")

        sku_aggregation = {}
        capital_by_platform = {p: 0.0 for p in all_platforms}

        # 1. First pass: Aggregate by SKU
        for prod, pred in data:
            sku = prod.sku or "unspecified"
            platform = prod.source_platform.value.upper() if prod.source_platform else "UNKNOWN"

            # Platform capital (always sum per product instance)
            val_cost = (prod.current_stock or 0) * (prod.cost_price or 0.0)
            if platform in capital_by_platform:
                capital_by_platform[platform] += val_cost

            if sku not in sku_aggregation:
                sku_aggregation[sku] = {
                    "product_id": prod.id,
                    "cost": prod.cost_price or 0.0,
                    "sale": prod.sale_price or 0.0,
                    "stock": 0, "risk_value": 0.0, "stockout_date": None,
                    "coverage_days": None, "title": prod.title,
                    "reorder_quantity": 0, "run_rate": 0.0,
                    "supplier_id": str(prod.supplier_id) if prod.supplier_id else None,
                    "platforms": {platform},
                }
            else:
                sku_aggregation[sku]["platforms"].add(platform)

            agg = sku_aggregation[sku]
            agg["stock"] += prod.current_stock or 0
            if pred:
                agg["run_rate"] += pred.run_rate or 0.0
                agg["reorder_quantity"] += pred.reorder_quantity or 0
                if pred.predicted_stockout_date and pred.reorder_quantity > 0:
                    agg["risk_value"] += pred.reorder_quantity * (prod.sale_price or 0.0)

        # 2. Second pass: risk scoring + KPIs + health score (pure functions — intelligence/)
        risk_items, avg_coverage = score_products(sku_aggregation)
        kpis = calculate_financial_kpis(sku_aggregation)
        stockout_count = sum(1 for a in sku_aggregation.values() if a["stock"] <= 0)
        health_score = calculate_health_score(
            revenue_at_risk=kpis.revenue_at_risk,
            total_run_rate=kpis.total_run_rate,
            avg_sale_price=kpis.avg_sale_price,
            avg_coverage_days=avg_coverage,
            stockout_count=stockout_count,
            total_skus=len(sku_aggregation),
        )

        top_risks = [
            {
                "product_id": item.product_id, "sku": item.sku, "title": item.title,
                "risk_value": item.risk_value, "stockout_date": item.stockout_date,
                "reorder_quantity": item.reorder_quantity, "days_of_stock": item.days_of_stock,
                "run_rate": item.run_rate, "supplier_id": item.supplier_id,
                "source_platform": item.source_platform,
                "cost_price": item.cost_price, "sale_price": item.sale_price,
            }
            for item in risk_items
        ]

        print(f"[DecisionCenter] Aggregated {len(sku_aggregation)} SKUs. Total Stock: {kpis.total_stock}, Total Cost: {kpis.inventory_value_cost}")

        return DecisionCenterOverview(
            kpis=FinancialKpiSchema(
                inventory_value_cost=kpis.inventory_value_cost,
                inventory_value_sale=kpis.inventory_value_sale,
                revenue_at_risk=kpis.revenue_at_risk,
                stock_coverage_avg_days=kpis.stock_coverage_avg_days,
                currency=currency, is_mutualized=is_mutualized
            ),
            top_risks=top_risks,
            total_run_rate=round(kpis.total_run_rate, 4),
            total_stock=kpis.total_stock,
            health_score=health_score,
            active_platforms=all_platforms,
            capital_breakdown=[{"platform": p, "value": round(v, 2)} for p, v in capital_by_platform.items() if v > 0],
            message=f"Omnicanal ({len(data)} prods, {kpis.total_stock} stock)"
        )
