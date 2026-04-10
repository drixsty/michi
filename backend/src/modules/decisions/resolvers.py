import strawberry
from typing import Optional
from strawberry.types import Info
from src.core.graphql.context import GraphQLContext
from src.core.exceptions import UnauthenticatedException
from src.modules.auth.models import User
from .types import DecisionCenterOverviewType, FinancialKpiType, TopRiskType
from .service import DecisionCenterService

@strawberry.type
class DecisionQuery:
    @strawberry.field
    async def financial_overview(self, info: Info[GraphQLContext, None]) -> DecisionCenterOverviewType:
        if not info.context.user_id:
            raise UnauthenticatedException()
        service = DecisionCenterService(info.context.db)
        overview = await service.get_overview(info.context.user_id)
        
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
                    product_id=strawberry.ID(str(r.get("product_id"))),
                    sku=r.get("sku", "N/A"),
                    title=r.get("title", "S/T"),
                    risk_value=r.get("risk_value", 0),
                    stockout_date=r.get("stockout_date"),
                    reorder_quantity=r.get("reorder_quantity", 0),
                    days_of_stock=r.get("days_of_stock", 0),
                    run_rate=r.get("run_rate", 0),
                    supplier_id=strawberry.ID(r["supplier_id"]) if r.get("supplier_id") else None,
                    source_platform=r.get("source_platform"),
                    cost_price=r.get("cost_price", 0),
                    sale_price=r.get("sale_price", 0),
                ) for r in overview.top_risks
            ],
            total_run_rate=overview.total_run_rate,
            total_stock=overview.total_stock,
            health_score=overview.health_score,
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
        if not info.context.user_id:
            raise UnauthenticatedException()
        db = info.context.db
        
        # On recharge l'utilisateur pour être sûr d'avoir la session
        user_db = await db.get(User, info.context.user_id)
        if not user_db:
            return False
            
        prefs = dict(user_db.preferences) if user_db.preferences else {}
        
        if currency is not None:
            prefs["currency"] = currency
        if is_mutualized is not None:
            prefs["is_mutualized"] = is_mutualized
            
        user_db.preferences = prefs
        await db.commit()
        return True
