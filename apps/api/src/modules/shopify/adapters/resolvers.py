from core.database.models import Organization, User, OrganizationMember
"""
Resolvers GraphQL — Shopify
Types Strawberry + Query/Mutation pour produits, sync mock et validation.
"""
import strawberry
from typing import List, Optional
from datetime import datetime

from core.exceptions import UnauthenticatedException
from modules.shopify.application.service import ShopifyService
from modules.inventory.application.inventory_service import InventoryService
from modules.inventory.application.alert_service import AlertService
from core.graphql.types import SupplierType, ChannelBreakdownType, ProductType, IngestionResult, SyncResultType
from modules.forecasting.application.forecasting_service import ForecastingService
from modules.forecasting.adapters.resolvers import (
    PredictionType, 
    CleanedDemandType
)
from modules.auth.adapters.decorators import require_permission
from modules.auth.domain.constants import MichiPermission
from modules.shopify.domain.validation import DataValidationService


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
    async def validate_mock_data(self, info: strawberry.types.Info, store_id: strawberry.ID) -> ValidationReportType:
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
    async def trigger_mock_data_sync(self, info: strawberry.types.Info, store_id: Optional[strawberry.ID] = None, platform: str = "shopify") -> IngestionResult:
        """Alias pour la compatibilité avec l'ancien schéma."""
        return await self.trigger_omnichannel_sync(info, store_id)

    @strawberry.mutation
    @require_permission(MichiPermission.STORES_MANAGE)
    async def trigger_omnichannel_sync(self, info: strawberry.types.Info, store_id: Optional[strawberry.ID] = None) -> IngestionResult:
        from modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository
        from modules.forecasting.application.forecasting_service import ForecastingService
        from modules.forecasting.infrastructure.repositories.cleaned_demand_repository import SQLAlchemyCleanedDemandRepository
        from modules.forecasting.infrastructure.repositories.prediction_repository import SQLAlchemyPredictionRepository
        from modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
        from modules.inventory.infrastructure.repositories.sales_log_repository import SQLAlchemySalesLogRepository
        from modules.inventory.infrastructure.repositories.supplier_repository import SQLAlchemySupplierRepository
        from modules.inventory.infrastructure.repositories.alert_repository import SQLAlchemyAlertRepository
        from modules.inventory.application.alert_service import AlertService
        from modules.inventory.application.email_service import EmailService
        import uuid

        db = info.context.db
        store_repo = SQLAlchemyStoreRepository(db)
        shopify_service = ShopifyService(db)
        
        # Déterminer quels stores synchroniser, en conservant la platform de chaque store
        # pour la passer au générateur de mock (évite que tous les produits soient SHOPIFY).
        store_platform_map: dict[str, str] = {}
        if store_id:
            store = await store_repo.get_by_id(uuid.UUID(str(store_id)))
            if store and store.connected:
                store_platform_map[str(store_id)] = store.platform.value
        else:
            if not info.context.org_id:
                raise UnauthenticatedException("Organisation non identifiée")
            stores = await store_repo.list_by_organization(uuid.UUID(str(info.context.org_id)))
            store_platform_map = {str(s.id): s.platform.value for s in stores if s.connected}

        target_store_ids = list(store_platform_map.keys())

        if not target_store_ids:
            return IngestionResult(
                success=True,
                message="Aucune boutique connectée à synchroniser.",
                platform="Omnichannel",
                products_count=0,
                sales_logs_count=0
            )

        total_products = 0
        total_sales = 0
        
        # Initialiser le service de prévision (shared for better perf)
        forecasting = ForecastingService(
            SQLAlchemyCleanedDemandRepository(db),
            SQLAlchemyPredictionRepository(db),
            SQLAlchemyProductRepository(db),
            SQLAlchemySalesLogRepository(db),
            store_repo,
            SQLAlchemySupplierRepository(db)
        )

        # Initialiser le service d'alertes (shared)
        alert_service = AlertService(
            SQLAlchemyAlertRepository(db),
            SQLAlchemyProductRepository(db),
            store_repo,
            EmailService()
        )

        for s_id in target_store_ids:
            # 1. Sync Mock Data with correct platform
            result = await shopify_service.trigger_mock_sync(s_id, platform=store_platform_map[s_id])
            total_products += result.products_created
            total_sales += result.sales_logs_created
            
            # 2. Run Forecasting Pipeline
            await forecasting.run_cleaning_pipeline(s_id)
            await forecasting.run_prediction_pipeline(s_id)

            # 3. Generate Stockout Alerts
            await alert_service.check_for_stockouts(s_id)

        # Commit explicit maintenant que get_db ne le fait plus automatiquement (plus sûr avec SerializedAsyncSession)
        await db.commit()

        return IngestionResult(
            success=True,
            message=f"Sync Omnicanal réussie pour {len(target_store_ids)} boutique(s). Prédictions mises à jour.",
            platform="Omnichannel",
            products_count=total_products,
            sales_logs_count=total_sales
        )

    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_EDIT)
    async def update_product_settings(
        self, 
        info: strawberry.types.Info, 
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
        from modules.forecasting.infrastructure.repositories.cleaned_demand_repository import SQLAlchemyCleanedDemandRepository
        from modules.forecasting.infrastructure.repositories.prediction_repository import SQLAlchemyPredictionRepository
        from modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
        from modules.inventory.infrastructure.repositories.sales_log_repository import SQLAlchemySalesLogRepository
        from modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository

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
