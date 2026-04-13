"""
Resolvers GraphQL — Forecasting
Queries : cleanedDemand, predictions, predictionForProduct
Mutations : runCleaningPipeline, runPredictionPipeline
"""
import strawberry
from typing import List, Optional
from datetime import date, datetime

from src.core.exceptions import UnauthenticatedException
from .service import ForecastingService


@strawberry.type
class CleanedDemandType:
    id: strawberry.ID
    product_id: strawberry.ID
    date: date
    raw_units_sold: float
    corrected_units_sold: float
    inventory_level: Optional[int] = None
    is_stockout: bool
    is_outlier: bool
    correction_type: str
    computed_at: datetime


@strawberry.type
class PipelineResultType:
    success: bool
    products_processed: int
    rows_written: int
    stockout_corrections: int
    outlier_corrections: int
    message: str


@strawberry.type
class PredictionType:
    id: strawberry.ID
    product_id: strawberry.ID
    run_rate: float
    days_of_stock: Optional[float]
    predicted_stockout_date: Optional[date]
    reorder_quantity: int
    current_stock_snapshot: float
    lead_time_snapshot: int
    moq_snapshot: int
    mape_score: Optional[float]
    computed_at: datetime


@strawberry.type
class PredictionRunResultType:
    success: bool
    products_processed: int
    message: str


@strawberry.type
class DashboardKPIType:
    total_products: int
    actual_stockouts: int
    urgent_alerts: int
    predicted_stockouts_30d: int
    message: str


@strawberry.type
class ForecastingQuery:
    @strawberry.field
    async def cleaned_demand(
        self,
        info,
        product_id: strawberry.ID,
        limit: int = 365,
    ) -> List[CleanedDemandType]:
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        rows = await service.get_cleaned_demand(str(product_id), limit=limit)

        return [
            CleanedDemandType(
                id=strawberry.ID(str(r.id)),
                product_id=strawberry.ID(str(r.product_id)),
                date=r.date,
                raw_units_sold=r.raw_units_sold,
                corrected_units_sold=r.corrected_units_sold,
                is_stockout=r.is_stockout,
                is_outlier=r.is_outlier,
                correction_type=r.correction_type,
                computed_at=r.computed_at,
            )
            for r in rows
        ]

    @strawberry.field
    async def predictions(self, info, store_id: Optional[strawberry.ID] = None) -> List[PredictionType]:
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        rows = await service.get_predictions(
            store_id=str(store_id) if store_id else None,
            organization_id=str(info.context.org_id) if not store_id else None
        )

        return [_prediction_to_type(r) for r in rows]

    @strawberry.field
    async def prediction_for_product(
        self,
        info,
        product_id: strawberry.ID,
    ) -> Optional[PredictionType]:
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        row = await service.get_prediction_for_product(str(product_id))

        if row is None:
            return None
        return _prediction_to_type(row)

    @strawberry.field
    async def dashboard_kpis(self, info, store_id: Optional[strawberry.ID] = None) -> DashboardKPIType:
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        res = await service.get_dashboard_kpis(
            store_id=str(store_id) if store_id else None,
            organization_id=str(info.context.org_id) if not store_id else None
        )

        return DashboardKPIType(
            total_products=res.total_products,
            actual_stockouts=res.actual_stockouts,
            urgent_alerts=res.urgent_alerts,
            predicted_stockouts_30d=res.predicted_stockouts_30d,
            message=res.message,
        )

    @strawberry.field
    async def replenishment_alerts(self, info, store_id: Optional[strawberry.ID] = None) -> List[PredictionType]:
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        rows = await service.get_replenishment_alerts(
            store_id=str(store_id) if store_id else None,
            organization_id=str(info.context.org_id) if not store_id else None
        )

        return [_prediction_to_type(r) for r in rows]


@strawberry.type
class ForecastingMutation:
    @strawberry.mutation
    async def run_cleaning_pipeline(self, info, store_id: strawberry.ID) -> PipelineResultType:
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        result = await service.run_cleaning_pipeline(str(store_id))

        return PipelineResultType(
            success=result.success,
            products_processed=result.products_processed,
            rows_written=result.rows_written,
            stockout_corrections=result.stockout_corrections,
            outlier_corrections=result.outlier_corrections,
            message=result.message,
        )

    @strawberry.mutation
    async def run_prediction_pipeline(self, info, store_id: strawberry.ID) -> PredictionRunResultType:
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        result = await service.run_prediction_pipeline(str(store_id))

        return PredictionRunResultType(
            success=result.success,
            products_processed=result.products_processed,
            message=result.message,
        )


def _prediction_to_type(r) -> PredictionType:
    return PredictionType(
        id=strawberry.ID(str(r.id)),
        product_id=strawberry.ID(str(r.product_id)),
        run_rate=r.run_rate,
        days_of_stock=r.days_of_stock,
        predicted_stockout_date=r.predicted_stockout_date,
        reorder_quantity=r.reorder_quantity,
        current_stock_snapshot=r.current_stock_snapshot,
        lead_time_snapshot=r.lead_time_snapshot,
        moq_snapshot=r.moq_snapshot,
        mape_score=r.mape_score,
        computed_at=r.computed_at,
    )
