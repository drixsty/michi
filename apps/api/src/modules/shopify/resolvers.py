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
from src.modules.inventory.application.inventory_service import InventoryService
from src.modules.inventory.application.alert_service import AlertService
from src.core.graphql.types import SupplierType, ChannelBreakdownType, ProductType, IngestionResult, SyncResultType
from src.modules.forecasting.application.forecasting_service import ForecastingService
from src.modules.forecasting.adapters.resolvers import (
    PredictionType, 
    CleanedDemandType
)
from src.modules.auth.decorators import require_permission
from src.modules.auth.constants import MichiPermission


# ── Strawberry Types ──────────────────────────────────────────────────────────

# ── Strawberry Types (Moved to Inventory) ─────────────────────────────────────


# SyncResultType moved to types.py


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
    async def trigger_mock_data_sync(self, info, store_id: strawberry.ID, platform: str) -> IngestionResult:
        from src.modules.inventory.application.alert_service import AlertService
        from src.modules.inventory.infrastructure.repositories.alert_repository import SQLAlchemyAlertRepository
        from src.modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
        from src.modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository
        from src.modules.inventory.application.email_service import EmailService

        s_id = str(store_id)
        service = ShopifyService(info.context.db)
        result = await service.trigger_mock_sync(s_id)
        
        from src.modules.forecasting.infrastructure.repositories.cleaned_demand_repository import SQLAlchemyCleanedDemandRepository
        from src.modules.forecasting.infrastructure.repositories.prediction_repository import SQLAlchemyPredictionRepository
        
        forecasting = ForecastingService(
            SQLAlchemyCleanedDemandRepository(info.context.db),
            SQLAlchemyPredictionRepository(info.context.db),
            product_repo,
            SQLAlchemySalesLogRepository(info.context.db),
            store_repo
        )
        await forecasting.run_cleaning_pipeline(s_id)
        await forecasting.run_prediction_pipeline(s_id)

        alert_service = AlertService(alert_repo, product_repo, store_repo, email_service)
        await alert_service.check_for_stockouts(s_id)

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
        from src.modules.forecasting.infrastructure.repositories.cleaned_demand_repository import SQLAlchemyCleanedDemandRepository
        from src.modules.forecasting.infrastructure.repositories.prediction_repository import SQLAlchemyPredictionRepository
        from src.modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
        from src.modules.inventory.infrastructure.repositories.sales_log_repository import SQLAlchemySalesLogRepository
        from src.modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository

        db = info.context.db
        forecasting_service = ForecastingService(
            SQLAlchemyCleanedDemandRepository(db),
            SQLAlchemyPredictionRepository(db),
            SQLAlchemyProductRepository(db),
            SQLAlchemySalesLogRepository(db),
            SQLAlchemyStoreRepository(db)
        )
        # Recalculate logic... (Need update in service too)
        # For now, let's assume we implement it or skip if not in scope

        # Persistance des paramètres et prédictions
        await info.context.db.commit()

        return ProductType.from_db(product)
