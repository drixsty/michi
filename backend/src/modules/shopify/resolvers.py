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
from src.modules.inventory.resolvers import SupplierType, ChannelBreakdownType


# ── Strawberry Types ──────────────────────────────────────────────────────────

@strawberry.type
class ProductType:
    id: strawberry.ID
    store_id: strawberry.ID
    sku: str
    title: str
    current_stock: int
    lead_time: int
    moq: int
    boost_factor: float
    stock_weight: float
    cost_price: Optional[float] = None
    sale_price: Optional[float] = None
    created_at: datetime
    prediction: Optional[PredictionType] = None
    supplier: Optional[SupplierType] = None
    warning_threshold: float = 0.0
    cleaned_demand: List[CleanedDemandType] = strawberry.field(default_factory=list)

    @strawberry.field
    async def channels(self, info) -> List[ChannelBreakdownType]:
        """Détail des stocks et run rate par canal de vente."""
        if not info.context.org_id:
            return []
        from src.modules.inventory.omnichannel_service import OmnichannelService
        service = OmnichannelService(info.context.db)
        return await service.get_channels_for_sku(self.sku, str(info.context.org_id))


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
    async def products(self, info, store_id: Optional[strawberry.ID] = None, id: Optional[strawberry.ID] = None) -> List[ProductType]:
        if not info.context.user_id:
            raise UnauthenticatedException()

        db = info.context.db
        if store_id:
            shop_ids = [str(store_id)]
        else:
            # Fallback omnichannel: tous les stores de l'organisation
            from src.modules.inventory.models import Store
            import uuid
            res = await db.execute(
                select(Store.id).where(Store.organization_id == uuid.UUID(str(info.context.org_id)))
            )
            shop_ids = [str(sid) for sid in res.scalars().all()]

        service = InventoryService(db)
        items = await service.get_products(shop_ids, product_id=str(id) if id else None)

        return [
            ProductType(
                id=strawberry.ID(str(p.id)),
                store_id=strawberry.ID(str(p.store_id)),
                sku=p.sku,
                title=p.title,
                current_stock=p.current_stock,
                lead_time=p.lead_time,
                moq=p.moq,
                boost_factor=p.boost_factor if p.boost_factor is not None else 1.0,
                stock_weight=p.stock_weight if p.stock_weight is not None else 1.0,
                cost_price=p.cost_price,
                sale_price=p.sale_price,
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
                         inventory_level=next((log.end_of_day_stock for log in p.sales_logs if log.date == r.date), None),
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
    async def trigger_mock_data_sync(self, info, store_id: strawberry.ID) -> SyncResultType:
        if not info.context.user_id:
            raise UnauthenticatedException()

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
        if not info.context.org_id:
            raise UnauthenticatedException()

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
            created_at=product.created_at,
        )
