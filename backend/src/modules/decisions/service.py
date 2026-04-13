from datetime import date
import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from src.modules.inventory.models import Product, PlatformSource, Store
from src.modules.forecasting.models import Prediction
from src.modules.auth.models import User, Organization
from loguru import logger
from .schemas import FinancialKpiSchema, DecisionCenterOverview

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
        
        inventory_value_cost, inventory_value_sale, revenue_at_risk = 0.0, 0.0, 0.0
        total_coverage_days, products_with_runrate = 0.0, 0
        total_run_rate, total_stock = 0.0, 0
        
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

        # 2. Second pass: Calculate unified SKU metrics and global totals
        top_risks = []
        from datetime import date, timedelta
        
        for sku, agg in sku_aggregation.items():
            # Unified SKU metrics
            if agg["run_rate"] > 0:
                agg["coverage_days"] = agg["stock"] / agg["run_rate"]
                agg["stockout_date"] = date.today() + timedelta(days=max(0, int(agg["coverage_days"])))
                # Global coverage aggregation
                total_coverage_days += agg["coverage_days"]
                products_with_runrate += 1
            else:
                agg["coverage_days"] = 999.0
                agg["stockout_date"] = None

            # Global KPI aggregation
            inventory_value_cost += agg["stock"] * agg["cost"]
            inventory_value_sale += agg["stock"] * agg["sale"]
            revenue_at_risk += agg["risk_value"]
            total_stock += agg["stock"]
            total_run_rate += agg["run_rate"]
            
            top_risks.append({
                "product_id": str(agg.get("product_id")), "sku": sku, "title": agg.get("title", "Sans titre"),
                "risk_value": round(agg.get("risk_value", 0), 2), "stockout_date": agg.get("stockout_date"),
                "reorder_quantity": agg.get("reorder_quantity", 0), "days_of_stock": round(agg.get("coverage_days") or 0, 1),
                "run_rate": round(agg.get("run_rate", 0), 4), "supplier_id": agg.get("supplier_id"),
                "source_platform": ",".join(sorted(list(agg["platforms"]))),
                "cost_price": round(agg.get("cost", 0), 2), "sale_price": round(agg.get("sale", 0), 2),
            })

        print(f"[DecisionCenter] Aggregated {len(sku_aggregation)} SKUs. Total Stock: {total_stock}, Total Cost: {inventory_value_cost}")

        avg_coverage = total_coverage_days / products_with_runrate if products_with_runrate > 0 else 0.0
        top_risks = sorted(top_risks, key=lambda x: x["risk_value"], reverse=True)

        # Health Score 3PI
        avg_sale_price = inventory_value_sale / total_stock if total_stock > 0 else 0.0
        forecasted_30d = total_run_rate * 30 * avg_sale_price
        total_pot = forecasted_30d + revenue_at_risk
        avail = 1.0 - (revenue_at_risk / total_pot) if total_pot > 0 else 1.0
        if avg_coverage < 7: rot = avg_coverage / 7
        elif 7 <= avg_coverage <= 45: rot = 1.0
        elif 45 < avg_coverage <= 90: rot = 1.0 - (avg_coverage - 45) / 45
        else: rot = max(0.0, 0.5 - (avg_coverage - 90) / 180)
        stockout_count = sum(1 for agg in sku_aggregation.values() if agg["stock"] <= 0)
        out_ratio = 1.0 - (stockout_count / len(sku_aggregation)) if sku_aggregation else 1.0
        health_score = max(0, min(100, round((avail * 0.5 + rot * 0.3 + out_ratio * 0.2) * 100)))

        return DecisionCenterOverview(
            kpis=FinancialKpiSchema(
                inventory_value_cost=round(inventory_value_cost, 2),
                inventory_value_sale=round(inventory_value_sale, 2),
                revenue_at_risk=round(revenue_at_risk, 2),
                stock_coverage_avg_days=round(avg_coverage, 1),
                currency=currency, is_mutualized=is_mutualized
            ),
            top_risks=top_risks,
            total_run_rate=round(total_run_rate, 4),
            total_stock=total_stock,
            health_score=health_score,
            active_platforms=all_platforms,
            capital_breakdown=[{"platform": p, "value": round(v, 2)} for p, v in capital_by_platform.items() if v > 0],
            message=f"Omnicanal ({len(data)} prods, {total_stock} stock)"
        )
