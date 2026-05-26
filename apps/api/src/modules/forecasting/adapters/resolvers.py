from core.database.models import Organization, User, OrganizationMember
"""
Forecasting Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""
import strawberry
from typing import List, Optional
import uuid

from modules.billing.adapters.decorators import require_plan
from modules.auth.adapters.decorators import require_permission
from modules.auth.domain.constants import MichiPermission
from core.graphql.types import (
    CleanedDemandType, PredictionType, 
    PipelineResultType, PredictionRunResultType, 
    DashboardKPIType
)



# Helpers for cross-module field resolution
async def resolve_cleaned_demands(info: strawberry.types.Info, product_id: str, sku: str) -> List[CleanedDemandType]:
    service = info.context.services.forecasting_service
    rows = await service.cleaned_demand_repo.list_by_product(uuid.UUID(product_id), limit=90)
    return [CleanedDemandType.from_db(r) for r in rows]

async def resolve_product_prediction(info: strawberry.types.Info, product_id: str, sku: str) -> Optional[PredictionType]:
    service = info.context.services.forecasting_service
    p = await service.prediction_repo.get_by_product(uuid.UUID(product_id))
    return PredictionType.from_db(p)

@strawberry.type
class ForecastingQuery:
    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def cleaned_demand(
        self,
        info: strawberry.types.Info,
        product_id: strawberry.ID,
        limit: int = 365,
    ) -> List[CleanedDemandType]:
        service = info.context.services.forecasting_service
        rows = await service.cleaned_demand_repo.list_by_product(uuid.UUID(str(product_id)), limit=limit)
        return [CleanedDemandType.from_db(r) for r in rows]

    @strawberry.field
    @require_plan("PRO")
    @require_permission(MichiPermission.FORECAST_VIEW)
    async def predictions(
        self,
        info: strawberry.types.Info,
        store_id: Optional[strawberry.ID] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[PredictionType]:
        _MAX_PAGE_SIZE = 500
        capped = min(max(1, limit), _MAX_PAGE_SIZE)
        service = info.context.services.forecasting_service
        rows = await service.get_predictions(
            org_id=str(info.context.org_id) if info.context.org_id else None,
            store_id=str(store_id) if store_id else None,
        )
        return [PredictionType.from_db(r) for r in rows[offset: offset + capped]]

    @strawberry.field
    @require_permission(MichiPermission.FORECAST_VIEW)
    async def dashboard_kpis(self, info: strawberry.types.Info, store_id: Optional[strawberry.ID] = None) -> DashboardKPIType:
        service = info.context.services.forecasting_service
        kpis = await service.get_dashboard_kpis(
            store_id=str(store_id) if store_id else None,
            organization_id=str(info.context.org_id) if info.context.org_id else None
        )
        return DashboardKPIType(
            total_products=kpis.total_products,
            actual_stockouts=kpis.actual_stockouts,
            urgent_alerts=kpis.urgent_alerts,
            predicted_stockouts_30d=kpis.predicted_stockouts_30d,
            message=kpis.message
        )

    @strawberry.field
    @require_plan("PRO")
    @require_permission(MichiPermission.FORECAST_VIEW)
    async def replenishment_alerts(self, info: strawberry.types.Info, store_id: Optional[strawberry.ID] = None) -> List[PredictionType]:
        """Alias de predictions pour la compatibilité avec le dashboard frontend."""
        return await self.predictions(info, store_id=store_id)

@strawberry.type
class ForecastingMutation:
    @strawberry.mutation
    @require_plan("PRO")
    @require_permission(MichiPermission.FORECAST_RUN)
    async def run_cleaning_pipeline(self, info: strawberry.types.Info, store_id: strawberry.ID) -> PipelineResultType:
        service = info.context.services.forecasting_service
        result = await service.run_cleaning_pipeline(str(store_id))
        await info.context.db.commit()
        return PipelineResultType(
            success=result.success,
            products_processed=result.products_processed,
            rows_written=result.rows_written,
            stockout_corrections=result.stockout_corrections,
            outlier_corrections=result.outlier_corrections,
            message=result.message
        )

    @strawberry.mutation
    @require_plan("PRO")
    @require_permission(MichiPermission.FORECAST_RUN)
    async def run_prediction_pipeline(self, info: strawberry.types.Info, store_id: strawberry.ID) -> PredictionRunResultType:
        service = info.context.services.forecasting_service
        result = await service.run_prediction_pipeline(str(store_id))
        await info.context.db.commit()
        return PredictionRunResultType(
            success=result.success,
            products_processed=result.products_processed,
            message=result.message
        )
