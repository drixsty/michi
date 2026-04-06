"""
Resolvers GraphQL — Shopify
Types Strawberry + Query/Mutation pour produits, sync mock et validation.
"""
import strawberry
from typing import List
from typing import List, Optional
from datetime import datetime

from src.core.exceptions import UnauthenticatedException
from .service import ShopifyService
from .validation import DataValidationService
from src.modules.forecasting.service import ForecastingService
from src.modules.forecasting.resolvers import (
    PredictionType, 
    _prediction_to_type, 
    CleanedDemandType
)
from src.modules.inventory.resolvers import SupplierType


# ── Strawberry Types ──────────────────────────────────────────────────────────

@strawberry.type
class ProductType:
    id: strawberry.ID
    shop_id: strawberry.ID
    sku: str
    title: str
    current_stock: int
    lead_time: int
    moq: int
    created_at: datetime
    prediction: Optional[PredictionType] = None
    supplier: Optional[SupplierType] = None
    warning_threshold: float = 0.0
    cleaned_demand: List[CleanedDemandType] = strawberry.field(default_factory=list)


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
    @strawberry.field
    async def products(self, info, id: Optional[strawberry.ID] = None) -> List[ProductType]:
        """
        Retourne tous les produits du shop connecté.
        Nécessite authentication (JWT).

        Example:
            query {
              products {
                id sku title currentStock leadTime moq
              }
            }
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ShopifyService(info.context.db)
        items = await service.get_products(info.context.shop_id, product_id=str(id) if id else None)

        return [
            ProductType(
                id=strawberry.ID(str(p.id)),
                shop_id=strawberry.ID(str(p.shop_id)),
                sku=p.sku,
                title=p.title,
                current_stock=p.current_stock,
                lead_time=p.lead_time,
                moq=p.moq,
                created_at=p.created_at,
                prediction=_prediction_to_type(p.__dict__['prediction']) if 'prediction' in p.__dict__ and p.__dict__['prediction'] else None,
                supplier=SupplierType(
                    id=strawberry.ID(str(p.supplier.id)),
                    name=p.supplier.name,
                    contact_email=p.supplier.contact_email,
                    reliability_score=p.supplier.reliability_score,
                    average_delay_days=p.supplier.average_delay_days
                ) if p.supplier else None,
                warning_threshold=(
                    p.__dict__['prediction'].run_rate * (p.lead_time + (p.supplier.average_delay_days if p.supplier else 0)) * 1.5
                ) if 'prediction' in p.__dict__ and p.__dict__['prediction'] else 0.0,
                cleaned_demand=[
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
                     for r in p.__dict__['cleaned_demands']
                 ] if 'cleaned_demands' in p.__dict__ and p.__dict__['cleaned_demands'] else [],
             )
            for p in items
        ]

    @strawberry.field
    async def validate_mock_data(self, info) -> ValidationReportType:
        """
        Valide la cohérence du dataset mock (R1–R6).
        Nécessite authentication (JWT).

        Example:
            query {
              validateMockData {
                isValid productCount salesLogCount stockoutRatio summary
                issues { rule severity detail }
              }
            }
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        validator = DataValidationService(info.context.db)
        report = await validator.validate(info.context.shop_id)

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
    async def trigger_mock_data_sync(self, info) -> SyncResultType:
        """
        Régénère un dataset mock complet (50 produits + 365j historique).
        Nécessite authentication (JWT).

        Example:
            mutation {
              triggerMockDataSync {
                success productsCreated salesLogsCreated message
              }
            }
        """
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ShopifyService(info.context.db)
        result = await service.trigger_mock_sync(info.context.shop_id)
        
        # ── Déclenchement automatique des prédictions (US 2.8) ────────────────
        # On relance le nettoyage et le calcul pour que le dashboard soit à jour
        forecasting = ForecastingService(info.context.db)
        await forecasting.run_cleaning_pipeline(info.context.shop_id)
        await forecasting.run_prediction_pipeline(info.context.shop_id)

        # Persistance globale
        await info.context.db.commit()

        return SyncResultType(
            success=result.success,
            products_created=result.products_created,
            sales_logs_created=result.sales_logs_created,
            message=result.message + " Prédictions recalculées.",
        )
    @strawberry.mutation
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
        if not info.context.shop_id:
            raise UnauthenticatedException()

        service = ShopifyService(info.context.db)
        product = await service.update_product_settings(
            shop_id=info.context.shop_id,
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
            shop_id=strawberry.ID(str(product.shop_id)),
            sku=product.sku,
            title=product.title,
            current_stock=product.current_stock,
            lead_time=product.lead_time,
            moq=product.moq,
            created_at=product.created_at,
        )
