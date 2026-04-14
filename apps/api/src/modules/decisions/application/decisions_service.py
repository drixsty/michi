"""
Application DecisionsService (DDD) — Sprint 21.
Coordinates analytics and decision-making logic using domain ports.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from loguru import logger

from src.modules.auth.domain.ports import IUserRepository
from src.modules.inventory.domain.ports import IProductRepository, IStoreRepository
from src.modules.forecasting.domain.ports import IPredictionRepository
from src.modules.inventory.domain.entities import PlatformSource
from src.modules.decisions.domain.entities import (
    DecisionCenterOverview, 
    FinancialKpis, 
    RiskItem
)
from src.modules.intelligence.analytics.financial_kpis import calculate_financial_kpis
from src.modules.intelligence.analytics.health_score import calculate_health_score
from src.modules.intelligence.analytics.risk_scoring import score_products

class ApplicationDecisionsService:
    def __init__(
        self,
        user_repo: IUserRepository,
        store_repo: IStoreRepository,
        product_repo: IProductRepository,
        prediction_repo: IPredictionRepository
    ):
        self._users = user_repo
        self._stores = store_repo
        self._products = product_repo
        self._predictions = prediction_repo

    async def get_overview(
        self, 
        user_id: str, 
        store_id: Optional[str] = None, 
        channel: Optional[str] = None
    ) -> DecisionCenterOverview:
        """
        Génère l'overview du Decision Center pour un utilisateur et une organisation.
        """
        u_uuid = UUID(str(user_id))
        user = await self._users.get_by_id(u_uuid)
        if not user:
            raise Exception("Utilisateur non trouvé")

        prefs = user.preferences or {}
        is_mutualized = prefs.get("is_mutualized", False)
        currency = prefs.get("currency", "€")

        if not user.current_organization_id:
            return self._empty_overview(currency, is_mutualized)

        org_uuid = user.current_organization_id

        # 1. Charger les stores
        all_stores = await self._stores.list_by_organization(org_uuid, connected_only=True)
        all_platforms = sorted(list(set(s.platform.value.upper() for s in all_stores)))
        active_store_ids = [s.id for s in all_stores]

        # 2. Charger les données (Produits + Prédictions)
        # On fetch tout pour l'organisation active
        products = await self._products.list_by_store(active_store_ids)
        predictions = await self._predictions.list_by_organization(org_uuid)
        
        # Indexer les prédictions par ID produit
        prediction_map = {str(p.product_id): p for p in predictions}

        # 3. Filtrage et Agrégation par SKU
        sku_aggregation = {}
        capital_by_platform = {p: 0.0 for p in all_platforms}

        # Filtrage par canal si spécifié
        target_platform = None
        if channel and channel.lower() != 'all':
            try:
                target_platform = PlatformSource(channel.upper())
            except ValueError:
                logger.warning(f"Invalid channel requested: {channel}")

        for prod in products:
            # Filtre plateforme
            if target_platform and prod.source_platform != target_platform:
                continue

            sku = prod.sku or "unspecified"
            platform = prod.source_platform.value.upper() if prod.source_platform else "UNKNOWN"
            pred = prediction_map.get(str(prod.id))

            # Capital par plateforme
            val_cost = (prod.current_stock or 0) * (prod.cost_price or 0.0)
            if platform in capital_by_platform:
                capital_by_platform[platform] += val_cost
            else:
                capital_by_platform[platform] = val_cost

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
                    "platforms": {platform},
                    "source_platform": platform # Pour le tracking dans le risk scoring
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
                
                # Mise à jour de la date de rupture la plus proche si nécessaire
                if pred.predicted_stockout_date:
                    if agg["stockout_date"] is None or pred.predicted_stockout_date < agg["stockout_date"]:
                        agg["stockout_date"] = pred.predicted_stockout_date
                
                # Jours de stock
                if pred.days_of_stock is not None:
                    if agg["coverage_days"] is None or pred.days_of_stock < agg["coverage_days"]:
                         agg["coverage_days"] = pred.days_of_stock

        # 4. Calculs via le module Intelligence
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
            RiskItem(
                product_id=item.product_id,
                sku=item.sku,
                title=item.title,
                risk_value=item.risk_value,
                stockout_date=str(item.stockout_date) if item.stockout_date else None,
                reorder_quantity=item.reorder_quantity,
                days_of_stock=item.days_of_stock,
                run_rate=item.run_rate,
                supplier_id=item.supplier_id,
                source_platform=item.source_platform,
                cost_price=item.cost_price,
                sale_price=item.sale_price,
            )
            for item in risk_items
        ]

        return DecisionCenterOverview(
            kpis=FinancialKpis(
                inventory_value_cost=kpis.inventory_value_cost,
                inventory_value_sale=kpis.inventory_value_sale,
                revenue_at_risk=kpis.revenue_at_risk,
                stock_coverage_avg_days=kpis.stock_coverage_avg_days,
                currency=currency,
                is_mutualized=is_mutualized
            ),
            top_risks=top_risks,
            total_run_rate=round(kpis.total_run_rate, 4),
            total_stock=kpis.total_stock,
            health_score=health_score,
            active_platforms=all_platforms,
            capital_breakdown=[{"platform": p, "value": round(v, 2)} for p, v in capital_by_platform.items() if v > 0],
            message=f"Omnicanal ({len(products)} prods, {kpis.total_stock} stock)"
        )

    def _empty_overview(self, currency: str, is_mutualized: bool) -> DecisionCenterOverview:
        return DecisionCenterOverview(
            kpis=FinancialKpis(0, 0, 0, 0, currency, is_mutualized),
            top_risks=[],
            total_run_rate=0.0,
            total_stock=0,
            health_score=0,
            active_platforms=[],
            capital_breakdown=[],
            message="Pas d'organisation active."
        )
