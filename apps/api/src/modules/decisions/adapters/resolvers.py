from core.database.models import Organization, User, OrganizationMember
"""
Decisions Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""
import strawberry
from typing import Optional, List
from strawberry.types import Info
from uuid import UUID

from core.graphql.context import GraphQLContext
from core.exceptions import UnauthenticatedException
from .graphql_types import (
    DecisionCenterOverviewType, 
    FinancialKpiType, 
    TopRiskType, 
    PlatformCapitalType
)

@strawberry.type
class DecisionQuery:
    @strawberry.field
    async def financial_overview(
        self, 
        info: Info[GraphQLContext, None], 
        store_id: Optional[strawberry.ID] = None, 
        channel: Optional[str] = None
    ) -> DecisionCenterOverviewType:
        """Récupère l'overview financière consolidée."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = info.context.services.decisions_service
        overview = await service.get_overview(
            user_id=info.context.user_id, 
            store_id=str(store_id) if store_id else None, 
            channel=channel
        )
        
        return DecisionCenterOverviewType(
            kpis=FinancialKpiType(
                inventory_value_cost=overview.kpis.inventory_value_cost,
                inventory_value_sale=overview.kpis.inventory_value_sale,
                revenue_at_risk=overview.kpis.revenue_at_risk,
                stock_coverage_avg_days=overview.kpis.stock_coverage_avg_days,
                currency=overview.kpis.currency,
                is_mutualized=overview.kpis.is_mutualized
            ),
            top_risks=[
                TopRiskType(
                    product_id=strawberry.ID(str(r.product_id)),
                    sku=r.sku,
                    title=r.title,
                    risk_value=r.risk_value,
                    stockout_date=r.stockout_date, # Assuming frontend handles string or it's formatted
                    reorder_quantity=r.reorder_quantity,
                    days_of_stock=r.days_of_stock,
                    run_rate=r.run_rate,
                    supplier_id=strawberry.ID(r.supplier_id) if r.supplier_id else None,
                    source_platform=r.source_platform,
                    cost_price=r.cost_price,
                    sale_price=r.sale_price,
                ) for r in overview.top_risks
            ],
            total_run_rate=overview.total_run_rate,
            total_stock=overview.total_stock,
            health_score=overview.health_score,
            active_platforms=overview.active_platforms,
            capital_breakdown=[
                PlatformCapitalType(platform=c["platform"], value=c["value"])
                for c in overview.capital_breakdown
            ],
            message=overview.message
        )

@strawberry.type
class DecisionMutation:
    @strawberry.mutation
    async def update_strategic_settings(
        self, 
        info: Info[GraphQLContext, None], 
        currency: Optional[str] = None, 
        is_mutualized: Optional[bool] = None
    ) -> bool:
        """Met à jour les préférences stratégiques (devise, mutualisation)."""
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        auth_service = info.context.services.auth_service
        user_id = UUID(str(info.context.user_id))
        
        # 1. Charger les préférences actuelles
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            return False
            
        prefs = dict(user.preferences or {})
        if currency is not None:
            prefs["currency"] = currency
        if is_mutualized is not None:
            prefs["is_mutualized"] = is_mutualized
            
        # 2. Sauvegarder via le service Auth
        await auth_service.update_user(user_id, preferences=prefs)
        return True
