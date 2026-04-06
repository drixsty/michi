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
        """
        Retourne la demande nettoyée pour un produit.
        Nécessite authentication (JWT).

        Example:
            query {
              cleanedDemand(productId: "uuid", limit: 30) {
                date rawUnitsSold correctedUnitsSold isStockout isOutlier correctionType
              }
            }
        """
        if not info.context.shop_id:
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
    async def predictions(self, info) -> List[PredictionType]:
        """
        Retourne les prédictions pour tous les produits du shop,
        triées par date de rupture prévisionnelle (les plus urgentes en premier).
        Nécessite authentication (JWT).

        Example:
            query {
              predictions {
                productId runRate daysOfStock predictedStockoutDate reorderQuantity
              }
            }
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        rows = await service.get_predictions(info.context.shop_id)

        return [_prediction_to_type(r) for r in rows]

    @strawberry.field
    async def prediction_for_product(
        self,
        info,
        product_id: strawberry.ID,
    ) -> Optional[PredictionType]:
        """
        Retourne la prédiction pour un produit spécifique, ou null si non calculée.
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        row = await service.get_prediction_for_product(str(product_id))

        if row is None:
            return None
        return _prediction_to_type(row)

    @strawberry.field
    async def dashboard_kpis(self, info) -> DashboardKPIType:
        """
        Retourne les indicateurs clés de performance du shop (US 3.5).
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        res = await service.get_dashboard_kpis(info.context.shop_id)

        return DashboardKPIType(
            total_products=res.total_products,
            actual_stockouts=res.actual_stockouts,
            urgent_alerts=res.urgent_alerts,
            predicted_stockouts_30d=res.predicted_stockouts_30d,
            message=res.message,
        )

    @strawberry.field
    async def replenishment_alerts(self, info) -> List[PredictionType]:
        """
        Retourne les alertes de réapprovisionnement (US 3.4).
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        rows = await service.get_replenishment_alerts(info.context.shop_id)

        return [_prediction_to_type(r) for r in rows]


@strawberry.type
class ForecastingMutation:
    @strawberry.mutation
    async def run_cleaning_pipeline(self, info) -> PipelineResultType:
        """
        Exécute la pipeline OOS + IQR sur tous les produits du shop.
        Nécessite authentication (JWT).

        Example:
            mutation {
              runCleaningPipeline {
                success productsProcessed rowsWritten
                stockoutCorrections outlierCorrections message
              }
            }
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        result = await service.run_cleaning_pipeline(info.context.shop_id)

        return PipelineResultType(
            success=result.success,
            products_processed=result.products_processed,
            rows_written=result.rows_written,
            stockout_corrections=result.stockout_corrections,
            outlier_corrections=result.outlier_corrections,
            message=result.message,
        )

    @strawberry.mutation
    async def run_prediction_pipeline(self, info) -> PredictionRunResultType:
        """
        Calcule le run rate + prédictions (stockout date + reorder qty) pour
        tous les produits du shop.
        Nécessite que runCleaningPipeline ait été exécuté au préalable.
        Nécessite authentication (JWT).

        Example:
            mutation {
              runPredictionPipeline {
                success productsProcessed message
              }
            }
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ForecastingService(info.context.db)
        result = await service.run_prediction_pipeline(info.context.shop_id)

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
        computed_at=r.computed_at,
    )
