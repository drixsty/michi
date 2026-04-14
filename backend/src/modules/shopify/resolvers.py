"""
Resolvers GraphQL — Shopify
Types Strawberry + Query/Mutation pour produits, sync mock et validation.
"""
import strawberry
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select

from src.core.exceptions import UnauthenticatedException
from .service import ShopifyService
from src.modules.inventory.service import InventoryService
from .validation import DataValidationService
from src.modules.forecasting.service import ForecastingService
from src.modules.forecasting.resolvers import (
    PredictionType, 
    _prediction_to_type, 
    CleanedDemandType
)
from src.modules.inventory.resolvers import SupplierType, ChannelBreakdownType, ProductType
from src.modules.auth.decorators import require_permission
from src.modules.auth.constants import MichiPermission


# ── Strawberry Types ──────────────────────────────────────────────────────────

# ── Strawberry Types (Moved to Inventory) ─────────────────────────────────────


@strawberry.type
class SyncResultType:
    success: bool
    products_created: int
    sales_logs_created: int
    message: str


@strawberry.type
class ValidationIssueType:
    rule: str
    severity: str
    detail: str


@strawberry.type
class ValidationReportType:
    is_valid: bool
    product_count: int
    sales_log_count: int
    stockout_ratio: float
    issues: List[ValidationIssueType]
    summary: str


# ── Query Extension ───────────────────────────────────────────────────────────

@strawberry.type
class ShopifyQuery:
    pass

    @strawberry.field
    async def validate_mock_data(self, info, store_id: strawberry.ID) -> ValidationReportType:
        if not info.context.user_id:
            raise UnauthenticatedException()

        validator = DataValidationService(info.context.db)
        report = await validator.validate(str(store_id))

        return ValidationReportType(
            is_valid=report.is_valid,
            product_count=report.product_count,
            sales_log_count=report.sales_log_count,
            stockout_ratio=report.stockout_ratio,
            issues=[
                ValidationIssueType(rule=i.rule, severity=i.severity, detail=i.detail)
                for i in report.issues
            ],
            summary=report.summary,
        )


# ── Mutation Extension ────────────────────────────────────────────────────────

@strawberry.type
class ShopifyMutation:
    @strawberry.mutation
    @require_permission(MichiPermission.STORES_MANAGE)
    async def trigger_mock_data_sync(self, info, store_id: strawberry.ID) -> SyncResultType:

        s_id = str(store_id)
        service = ShopifyService(info.context.db)
        result = await service.trigger_mock_sync(s_id)
        
        forecasting = ForecastingService(info.context.db)
        await forecasting.run_cleaning_pipeline(s_id)
        await forecasting.run_prediction_pipeline(s_id)

        from src.modules.inventory.alert_service import AlertService
        alerts = AlertService(info.context.db)
        await alerts.check_for_stockouts(s_id)

        # Persistance globale
        await info.context.db.commit()

        return SyncResultType(
            success=result.success,
            products_created=result.products_created,
            sales_logs_created=result.sales_logs_created,
            message=result.message + " Prédictions et alertes mises à jour.",
        )

    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_EDIT)
    async def update_product_settings(
        self, 
        info, 
        id: strawberry.ID, 
        lead_time: int = None, 
        moq: int = None
    ) -> ProductType:
        """
        Met à jour les paramètres logistiques d'un produit (Lead Time, MOQ).
        Nécessite authentication (JWT).
        """

        service = InventoryService(info.context.db)
        product = await service.update_product_settings(
            product_id=str(id),
            lead_time=lead_time,
            moq=moq
        )

        # Recalculer la prédiction en temps réel
        forecasting_service = ForecastingService(info.context.db)
        await forecasting_service.recalculate_prediction_for_product(str(product.id))

        # Persistance des paramètres et prédictions
        await info.context.db.commit()

        return ProductType(
            id=strawberry.ID(str(product.id)),
            store_id=strawberry.ID(str(product.store_id)),
            sku=product.sku,
            title=product.title,
            current_stock=product.current_stock,
            lead_time=product.lead_time,
            moq=product.moq,
            boost_factor=product.boost_factor if product.boost_factor is not None else 1.0,
            stock_weight=product.stock_weight if product.stock_weight is not None else 1.0,
            cost_price=product.cost_price,
            sale_price=product.sale_price,
            supplier_id=product.supplier_id
        )
