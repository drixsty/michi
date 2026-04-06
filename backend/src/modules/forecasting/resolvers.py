"""
Resolvers GraphQL — Forecasting
Query cleanedDemand + Mutation runCleaningPipeline.
"""
import strawberry
from typing import List
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
