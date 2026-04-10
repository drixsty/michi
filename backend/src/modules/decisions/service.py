from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from src.modules.inventory.models import Product
from src.modules.forecasting.models import Prediction
from src.modules.auth.models import User
from .schemas import FinancialKpiSchema, DecisionCenterOverview

class DecisionCenterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, user_id: str) -> DecisionCenterOverview:
        """
        Calcule les KPIs financiers globaux pour l'utilisateur.
        Prend en compte la mutualisation si configurée dans les préférences.
        Sprint 14 : enrichi avec run_rate, reorder_quantity, health_score.
        """
        # 1. Charger l'utilisateur et ses préférences
        user_res = await self.db.execute(select(User).where(User.id == user_id))
        user = user_res.scalars().first()
        if not user:
            raise Exception("Utilisateur non trouvé")

        # Extraction des préférences
        prefs = user.preferences or {}
        is_mutualized = prefs.get("is_mutualized", False)
        currency = prefs.get("currency", "€")

        # 2. Définition du filtre (Shop spécifique ou Organisation complète)
        shop_ids = [user.shop_id]
        
        if is_mutualized and user.organization_id:
            org_shops_res = await self.db.execute(
                select(User.shop_id).where(User.organization_id == user.organization_id)
            )
            shop_ids = org_shops_res.scalars().all()

        product_filter = Product.shop_id.in_(shop_ids)

        # 3. Charger les produits et leurs prédictions
        stmt = (
            select(Product, Prediction)
            .outerjoin(Prediction, Product.id == Prediction.product_id)
            .where(product_filter)
        )
        res = await self.db.execute(stmt)
        data = res.all()

        # Map pour regrouper par SKU
        sku_aggregation = {}
        
        # Initialisation des compteurs globaux
        inventory_value_cost = 0.0
        inventory_value_sale = 0.0
        revenue_at_risk = 0.0
        total_coverage_days = 0.0
        products_with_runrate = 0
        total_run_rate = 0.0
        total_stock = 0
        top_risks = []
        
        # 4. Premier passage : Agrégation par SKU
        for prod, pred in data:
            sku = prod.sku or "unspecified"
            if sku not in sku_aggregation:
                sku_aggregation[sku] = {
                    "product_id": prod.id,
                    "cost": prod.cost_price or 0.0,
                    "sale": prod.sale_price or 0.0,
                    "stock": 0,
                    "risk_value": 0.0,
                    "stockout_date": None,
                    "coverage_days": None,
                    "title": prod.title,
                    "reorder_quantity": 0,
                    "run_rate": 0.0,
                    "supplier_id": str(prod.supplier_id) if prod.supplier_id else None,
                    "source_platform": prod.source_platform.value if prod.source_platform else None,
                }
            
            agg = sku_aggregation[sku]
            agg["stock"] += prod.current_stock or 0
            
            if pred:
                agg["run_rate"] = max(agg["run_rate"], pred.run_rate or 0.0)
                agg["reorder_quantity"] += pred.reorder_quantity or 0

                if pred.predicted_stockout_date and pred.reorder_quantity > 0:
                    risk_val = pred.reorder_quantity * (prod.sale_price or 0.0)
                    agg["risk_value"] += risk_val
                    if not agg["stockout_date"] or pred.predicted_stockout_date < agg["stockout_date"]:
                        agg["stockout_date"] = pred.predicted_stockout_date
                
                if pred.days_of_stock is not None:
                    if agg["coverage_days"] is None:
                        agg["coverage_days"] = pred.days_of_stock
                    else:
                        agg["coverage_days"] = (agg["coverage_days"] + pred.days_of_stock) / 2

        # Calcul des KPIs globaux depuis l'agrégation
        for sku, agg in sku_aggregation.items():
            inventory_value_cost += agg["stock"] * agg["cost"]
            inventory_value_sale += agg["stock"] * agg["sale"]
            revenue_at_risk += agg["risk_value"]
            total_stock += agg["stock"]
            total_run_rate += agg["run_rate"]
            
            # Tous les produits sont inclus dans top_risks (pas seulement ceux avec risk > 0)
            # Le frontend filtrera par statut
            top_risks.append({
                "product_id": str(agg.get("product_id")),
                "sku": sku,
                "title": agg.get("title", "Sans titre"),
                "risk_value": round(agg.get("risk_value", 0), 2),
                "stockout_date": agg.get("stockout_date"),
                "reorder_quantity": agg.get("reorder_quantity", 0),
                "days_of_stock": round(agg.get("coverage_days") or 0, 1),
                "run_rate": round(agg.get("run_rate", 0), 4),
                "supplier_id": agg.get("supplier_id"),
                "source_platform": agg.get("source_platform"),
                "cost_price": round(agg.get("cost", 0), 2),
                "sale_price": round(agg.get("sale", 0), 2),
            })
            
            if agg["coverage_days"] is not None:
                total_coverage_days += agg["coverage_days"]
                products_with_runrate += 1

        # Moyenne de couverture
        avg_coverage = total_coverage_days / products_with_runrate if products_with_runrate > 0 else 0.0

        # Trier les risques par valeur décroissante
        top_risks = sorted(top_risks, key=lambda x: x["risk_value"], reverse=True)

        # Health Score (US 14.5)
        stock_efficiency = 1 - (revenue_at_risk / inventory_value_sale) if inventory_value_sale > 0 else 1.0
        coverage_score = min(avg_coverage / 30, 1.0) if avg_coverage > 0 else 0.0
        health_score = round(max(0, min(100, (stock_efficiency * 0.6 + coverage_score * 0.4) * 100)))

        kpis = FinancialKpiSchema(
            inventory_value_cost=round(inventory_value_cost, 2),
            inventory_value_sale=round(inventory_value_sale, 2),
            revenue_at_risk=round(revenue_at_risk, 2),
            stock_coverage_avg_days=round(avg_coverage, 1),
            currency=currency,
            is_mutualized=is_mutualized
        )

        return DecisionCenterOverview(
            kpis=kpis,
            top_risks=top_risks,
            total_run_rate=round(total_run_rate, 4),
            total_stock=total_stock,
            health_score=health_score,
            message="Données stratégiques calculées en temps réel."
        )
