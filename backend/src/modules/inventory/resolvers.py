import csv
import io
import strawberry
from typing import List, Optional, TYPE_CHECKING, Annotated
from datetime import datetime
import uuid
from sqlalchemy import select

if TYPE_CHECKING:
    from src.modules.forecasting.resolvers import CleanedDemandType, PredictionType

from src.core.exceptions import UnauthenticatedException
from loguru import logger
from .service import InventoryService
from .alert_service import AlertService
from .supplier_service import SupplierService
from .omnichannel_service import OmnichannelService

@strawberry.type
class AlertType:
    id: strawberry.ID
    product_id: strawberry.ID
    type: str
    message: str
    is_read: bool
    severity: int
    created_at: datetime

@strawberry.type
class SupplierType:
    id: strawberry.ID
    name: str
    contact_email: Optional[str]
    reliability_score: float
    average_delay_days: float

@strawberry.type
class PurchaseOrderType:
    id: strawberry.ID
    product_id: strawberry.ID
    supplier_id: strawberry.ID
    quantity: int
    order_date: str
    expected_arrival_date: str
    actual_arrival_date: Optional[str]
    status: str

@strawberry.type
class ProductType:
    id: strawberry.ID
    store_id: strawberry.ID
    title: str
    sku: str
    lead_time: int
    moq: int
    current_stock: int
    boost_factor: float
    stock_weight: float
    cost_price: Optional[float]
    sale_price: Optional[float]
    supplier_id: Optional[strawberry.ID] = None

    @strawberry.field(name="cleanedDemands")
    async def cleaned_demands(self, info) -> List[Annotated["CleanedDemandType", strawberry.lazy("src.modules.forecasting.resolvers")]]:
        try:
            from src.modules.forecasting.service import ForecastingService
            from src.modules.inventory.models import SalesLog
            from src.modules.forecasting.resolvers import CleanedDemandType
            from sqlalchemy import select
            
            service = ForecastingService(info.context.db)
            rows = await service.get_cleaned_demand(str(self.id))
            
            if not rows:
                # Fallback: Données brutes si la pipeline forecasting n'a pas encore tourné
                res = await info.context.db.execute(
                    select(SalesLog).where(SalesLog.product_id == uuid.UUID(str(self.id))).order_by(SalesLog.date.desc()).limit(90)
                )
                raw_logs = res.scalars().all()
                return [
                    CleanedDemandType(
                        id=strawberry.ID(str(r.id)),
                        product_id=strawberry.ID(str(r.product_id)),
                        date=r.date,
                        raw_units_sold=r.units_sold,
                        corrected_units_sold=r.units_sold,
                        inventory_level=r.end_of_day_stock,
                        is_stockout=False,
                        is_outlier=False,
                        correction_type="raw",
                        computed_at=datetime.utcnow()
                    )
                    for r in raw_logs
                ]

            return [
                CleanedDemandType(
                    id=strawberry.ID(str(r.id)),
                    product_id=strawberry.ID(str(r.product_id)),
                    date=r.date,
                    raw_units_sold=r.raw_units_sold,
                    corrected_units_sold=r.corrected_units_sold,
                    inventory_level=r.inventory_level,
                    is_stockout=r.is_stockout,
                    is_outlier=r.is_outlier,
                    correction_type=r.correction_type,
                    computed_at=r.computed_at,
                )
                for r in rows
            ]
        except Exception as e:
            logger.error(f"[GraphQL] Error in cleanedDemands resolver for {self.sku}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    @strawberry.field
    async def channels(self, info) -> List[Annotated["ChannelBreakdownType", strawberry.lazy("src.modules.inventory.resolvers")]]:
        try:
            from src.modules.inventory.service import InventoryService
            from src.modules.inventory.models import Store
            from sqlalchemy import select
            import uuid
            
            db = info.context.db
            org_id = info.context.org_id
            if not org_id:
                return []
            
            # 1. Trouver tous les shop_ids de l'org
            res = await db.execute(
                select(Store.id).where(Store.organization_id == uuid.UUID(str(org_id)))
            )
            shop_ids = [str(sid) for sid in res.scalars().all()]
            
            # 2. Trouver tous les produits avec le même SKU dans ces shops (Omnichannel logic)
            service = InventoryService(db)
            items = await service.get_products(shop_ids, product_id=self.sku)
            
            return [
                ChannelBreakdownType(
                    platform=p.source_platform.value if p.source_platform else "UNKNOWN",
                    product_id=strawberry.ID(str(p.id)),
                    current_stock=p.current_stock,
                    lead_time=p.lead_time,
                    moq=p.moq,
                    run_rate=p.prediction.run_rate if p.prediction else 0.0,
                    stock_weight=p.stock_weight
                )
                for p in items
            ]
        except Exception as e:
            logger.error(f"[GraphQL] Error in channels resolver for {self.sku}: {e}")
            return []

    @strawberry.field
    async def prediction(self, info) -> Optional[Annotated["PredictionType", strawberry.lazy("src.modules.forecasting.resolvers")]]:
        try:
            from src.modules.forecasting.resolvers import _prediction_to_type
            from src.modules.forecasting.service import ForecastingService
            service = ForecastingService(info.context.db)
            row = await service.get_prediction_for_product(str(self.id))
            
            if not row:
                return None
            return _prediction_to_type(row)
        except Exception as e:
            logger.error(f"[GraphQL] Error in prediction resolver for {self.sku}: {e}")
            return None

    @strawberry.field
    async def supplier(self, info) -> Optional[SupplierType]:
        try:
            from src.modules.inventory.models import Supplier
            from sqlalchemy import select
            import uuid
            if not hasattr(self, "supplier_id") or not self.supplier_id:
                return None
            
            s_id = uuid.UUID(str(self.supplier_id))
            result = await info.context.db.execute(
                select(Supplier).where(Supplier.id == s_id)
            )
            s = result.scalar_one_or_none()
            if not s:
                return None
            return SupplierType(
                id=strawberry.ID(str(s.id)),
                name=s.name,
                contact_email=s.contact_email,
                reliability_score=s.reliability_score,
                average_delay_days=s.average_delay_days
            )
        except Exception as e:
            logger.error(f"[GraphQL] Error in supplier resolver for {self.sku}: {e}")
            return None

    @strawberry.field
    async def warning_threshold(self, info) -> float:
        """Seuil d'alerte : run_rate * (lead_time + avg_delay) * 1.5"""
        pred = await self.prediction(info)
        supp = await self.supplier(info)
        if not pred:
            return 0.0
        
        effective_lt = self.lead_time + (supp.average_delay_days if supp else 1)
        return pred.run_rate * effective_lt * 1.5

@strawberry.type
class IngestionResult:
    success: bool
    message: str
    platform: str
    products_count: int
    sales_logs_count: int


# ── Omnichannel types (US 9.1 / 9.3) ──────────────────────────────────────────

@strawberry.type
class ChannelBreakdownType:
    """Stock disponible sur un canal spécifique pour un SKU donné."""
    platform: str
    product_id: strawberry.ID
    current_stock: int
    lead_time: int
    moq: int
    run_rate: float
    stock_weight: float


@strawberry.type
class OmnichannelProductType:
    """Vue agrégée d'un SKU sur toutes les plateformes (US 9.1)."""
    id: strawberry.ID
    sku: str
    title: str
    total_stock: int
    channel_count: int
    has_conflict: bool
    dominant_run_rate: float
    total_reorder_quantity: int
    predicted_stockout_date: Optional[str]
    abc_rank: str
    annual_gross_profit: float
    channels: List[ChannelBreakdownType]


@strawberry.type
class InventoryQuery:
    @strawberry.field
    async def products(self, info, store_id: Optional[strawberry.ID] = None, id: Optional[strawberry.ID] = None) -> List[ProductType]:
        if not info.context.user_id:
            raise UnauthenticatedException()

        db = info.context.db
        if store_id:
            shop_ids = [str(store_id)]
        else:
            # Fallback omnichannel: tous les stores de l'organisation
            org_id = info.context.org_id
            if not org_id:
                return []
            
            from src.modules.inventory.models import Store
            try:
                res = await db.execute(
                    select(Store.id).where(Store.organization_id == uuid.UUID(str(org_id)))
                )
                shop_ids = [str(sid) for sid in res.scalars().all()]
            except Exception as e:
                return []

        from .service import InventoryService
        service = InventoryService(db)
        items = await service.get_products(shop_ids, product_id=str(id) if id else None)

        return [
            ProductType(
                id=strawberry.ID(str(p.id)),
                store_id=strawberry.ID(str(p.store_id)),
                title=p.title,
                sku=p.sku,
                lead_time=p.lead_time,
                moq=p.moq,
                current_stock=p.current_stock,
                boost_factor=p.boost_factor if p.boost_factor is not None else 1.0,
                stock_weight=p.stock_weight if p.stock_weight is not None else 1.0,
                cost_price=p.cost_price,
                sale_price=p.sale_price,
                supplier_id=strawberry.ID(str(p.supplier_id)) if p.supplier_id else None
            )
            for p in items
        ]

    @strawberry.field
    async def unread_alerts(self, info, store_id: Optional[strawberry.ID] = None) -> List[AlertType]:
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        from .alert_service import AlertService
        alert_service = AlertService(info.context.db)
        alerts = await alert_service.get_unread_alerts(
            store_id=str(store_id) if store_id else None,
            organization_id=str(info.context.org_id) if not store_id else None
        )
        
        return [
            AlertType(
                id=strawberry.ID(str(a.id)),
                product_id=strawberry.ID(str(a.product_id)),
                type=a.type,
                message=a.message,
                is_read=a.is_read,
                severity=a.severity,
                created_at=a.created_at
            ) for a in alerts
        ]

    @strawberry.field
    async def suppliers(self, info, store_id: strawberry.ID) -> List[SupplierType]:
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        service = SupplierService(info.context.db)
        suppliers = await service.get_suppliers(str(store_id))
        
        return [
            SupplierType(
                id=strawberry.ID(str(s.id)),
                name=s.name,
                contact_email=s.contact_email,
                reliability_score=s.reliability_score,
                average_delay_days=s.average_delay_days
            ) for s in suppliers
        ]

    @strawberry.field
    async def omnichannel_inventory(self, info) -> List[OmnichannelProductType]:
        """Vue unifiée de l'organisation active (US 9.1 / 9.5)."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()

        service = OmnichannelService(info.context.db)
        items = await service.get_omnichannel_inventory(str(info.context.org_id))

        return [
            OmnichannelProductType(
                id=strawberry.ID(item.channels[0].product_id) if item.channels else strawberry.ID(item.sku),
                sku=item.sku,
                title=item.title,
                total_stock=item.total_stock,
                channel_count=item.channel_count,
                has_conflict=item.has_conflict,
                dominant_run_rate=item.dominant_run_rate,
                total_reorder_quantity=item.total_reorder_quantity,
                predicted_stockout_date=(
                    str(item.predicted_stockout_date)
                    if item.predicted_stockout_date else None
                ),
                abc_rank=item.abc_rank,
                annual_gross_profit=item.annual_gross_profit,
                channels=[
                    ChannelBreakdownType(
                        platform=ch.platform,
                        product_id=strawberry.ID(ch.product_id),
                        current_stock=ch.current_stock,
                        lead_time=ch.lead_time,
                        moq=ch.moq,
                        run_rate=ch.run_rate,
                        stock_weight=ch.stock_weight if ch.stock_weight is not None else 1.0,
                    )
                    for ch in item.channels
                ],
            )
            for item in items
        ]

    @strawberry.field
    async def export_replenishment_csv(self, info, store_id: strawberry.ID) -> str:
        """Génère le CSV de réapprovisionnement pour un Store."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = OmnichannelService(info.context.db)
        rows = await service.get_replenishment_export_data(str(store_id))

        output = io.StringIO()
        fieldnames = ["sku", "title", "platform", "current_stock", "run_rate", "days_of_stock", "predicted_stockout_date", "reorder_quantity", "lead_time", "moq"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()


@strawberry.type
class InventoryMutation:
    @strawberry.mutation
    async def ingest_csv_data(
        self, 
        info, 
        store_id: strawberry.ID,
        csv_content: str, 
        sku_col: str = "sku",
        date_col: str = "date",
        sales_col: str = "sales",
        stock_col: str = "stock",
        title_col: str = "title"
    ) -> IngestionResult:
        if not info.context.user_id:
            raise UnauthenticatedException()

        from src.modules.ingestion.service import IngestionService
        from src.modules.ingestion.connectors.csv import CSVConnector
        
        ingestion_service = IngestionService(info.context.db)
        ingestion_service.register_connector("csv", CSVConnector())
        
        mapping = {"sku": sku_col, "date": date_col, "units_sold": sales_col, "stock": stock_col, "title": title_col}
        
        result = await ingestion_service.ingest_from_platform(
            platform="csv",
            shop_id=str(store_id),
            csv_content=csv_content,
            mapping=mapping
        )
        
        from src.modules.forecasting.service import ForecastingService
        forecasting_service = ForecastingService(info.context.db)
        await forecasting_service.run_cleaning_pipeline(str(store_id))
        await forecasting_service.run_prediction_pipeline(str(store_id))
        
        from .alert_service import AlertService
        await AlertService(info.context.db).check_for_stockouts(str(store_id))

        return IngestionResult(success=True, message="Import CSV réussi.", platform="csv", products_count=result["products_count"], sales_logs_count=result["sales_logs_count"])

    @strawberry.mutation
    async def mark_alert_as_read(self, info, alert_id: strawberry.ID) -> bool:
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        from sqlalchemy import update
        from .models import Alert
        
        await info.context.db.execute(
            update(Alert)
            .where(Alert.id == uuid.UUID(str(alert_id)))
            .values(is_read=True)
        )
        await info.context.db.flush()
        return True

    @strawberry.mutation
    async def delete_alert(self, info, alert_id: strawberry.ID) -> bool:
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        from sqlalchemy import delete
        from .models import Alert
        
        await info.context.db.execute(
            delete(Alert)
            .where(Alert.id == uuid.UUID(str(alert_id)))
        )
        await info.context.db.flush()
        return True

    @strawberry.mutation
    async def create_purchase_order(self, info, store_id: strawberry.ID, product_id: strawberry.ID, supplier_id: strawberry.ID, quantity: int, expected_days: int = 14) -> PurchaseOrderType:
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        from .models import Product, Supplier, PurchaseOrder
        from datetime import date, timedelta
        
        po = PurchaseOrder(
            store_id=uuid.UUID(str(store_id)),
            product_id=uuid.UUID(str(product_id)),
            supplier_id=uuid.UUID(str(supplier_id)),
            quantity=quantity,
            expected_arrival_date=date.today() + timedelta(days=expected_days),
            status="PENDING"
        )
        info.context.db.add(po)
        await info.context.db.flush()

        # Email logic same...
        return PurchaseOrderType(id=strawberry.ID(str(po.id)), product_id=strawberry.ID(str(po.product_id)), supplier_id=strawberry.ID(str(po.supplier_id)), quantity=po.quantity, order_date=str(po.order_date), expected_arrival_date=str(po.expected_arrival_date), actual_arrival_date=None, status=po.status)

    @strawberry.mutation
    async def ingest_woocommerce_data(self, info, store_id: strawberry.ID, products_csv: str, orders_csv: str = "") -> IngestionResult:
        if not info.context.user_id:
            raise UnauthenticatedException()

        from .models import PlatformSource
        from src.modules.ingestion.service import IngestionService
        from src.modules.ingestion.connectors.woocommerce import WooCommerceConnector

        ingestion_service = IngestionService(info.context.db)
        ingestion_service.register_connector("woocommerce", WooCommerceConnector())

        result = await ingestion_service.ingest_from_platform(
            platform="woocommerce",
            shop_id=str(store_id),
            csv_content=products_csv,
            orders_csv=orders_csv or None,
            mapping={},
            source_platform=PlatformSource.WOOCOMMERCE,
        )

        from src.modules.forecasting.service import ForecastingService
        forecasting_service = ForecastingService(info.context.db)
        await forecasting_service.run_cleaning_pipeline(str(store_id))
        await forecasting_service.run_prediction_pipeline(str(store_id))

        from .alert_service import AlertService as _AlertService
        await _AlertService(info.context.db).check_for_stockouts(str(store_id))

        return IngestionResult(success=True, message="Import WooCommerce réussi.", platform="woocommerce", products_count=result.get("products_count", 0), sales_logs_count=result.get("sales_logs_count", 0))

    @strawberry.mutation
    async def receive_purchase_order(self, info, po_id: strawberry.ID) -> bool:
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        from .models import PurchaseOrder
        from sqlalchemy import select
        from datetime import date
        
        # 1. Marquer comme reçu
        result = await info.context.db.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == uuid.UUID(str(po_id)))
        )
        po = result.scalar_one()
        po.status = "RECEIVED"
        po.actual_arrival_date = date.today()
        
        await info.context.db.flush()
        
        # 2. Mettre à jour les stats fournisseur
        service = SupplierService(info.context.db)
        await service.update_supplier_performance(po.supplier_id)
        
        return True

    @strawberry.mutation
    async def update_product_settings(
        self,
        info,
        id: strawberry.ID,
        lead_time: Optional[int] = None,
        moq: Optional[int] = None,
        boost_factor: Optional[float] = None,
        stock_weight: Optional[float] = None,
        cost_price: Optional[float] = None,
        sale_price: Optional[float] = None
    ) -> ProductType:
        if not info.context.user_id:
            raise UnauthenticatedException()

        from .service import InventoryService
        service = InventoryService(info.context.db)
        
        product = await service.update_product_settings(
            product_id=str(id),
            lead_time=lead_time,
            moq=moq,
            boost_factor=boost_factor,
            stock_weight=stock_weight,
            cost_price=cost_price,
            sale_price=sale_price
        )

        return ProductType(
            id=strawberry.ID(str(product.id)),
            title=product.title,
            sku=product.sku,
            lead_time=product.lead_time,
            moq=product.moq,
            current_stock=product.current_stock,
            boost_factor=product.boost_factor if product.boost_factor is not None else 1.0,
            stock_weight=product.stock_weight if product.stock_weight is not None else 1.0,
            cost_price=product.cost_price,
            sale_price=product.sale_price
        )

    @strawberry.mutation(name="triggerOmnichannelSync")
    async def trigger_omnichannel_sync(self, info, store_id: Optional[strawberry.ID] = None) -> IngestionResult:
        """
        Déclenche la synchronisation pour un Store spécifique ou toute l'organisation.
        """
        if not info.context.user_id:
            raise UnauthenticatedException()

        from src.modules.inventory.models import Store
        from src.modules.shopify.service import ShopifyService 
        from src.modules.forecasting.service import ForecastingService
        from .alert_service import AlertService
        from sqlalchemy import select
        from datetime import datetime
        import uuid

        # 1. Identifier les Stores à synchroniser
        if store_id:
            result = await info.context.db.execute(
                select(Store).where(
                    Store.id == uuid.UUID(str(store_id)),
                    Store.connected == True
                )
            )
            stores = [result.scalar_one_or_none()]
            if not stores[0]:
                return IngestionResult(
                    success=False,
                    message="Store non trouvé ou non connecté.",
                    platform="none",
                    products_count=0,
                    sales_logs_count=0
                )
        else:
            # Sync all connected stores of the active organization
            if not info.context.org_id:
                return IngestionResult(success=False, message="Aucune organisation active.", platform="none", products_count=0, sales_logs_count=0)
            
            org_id = uuid.UUID(str(info.context.org_id))
            result = await info.context.db.execute(
                select(Store).where(
                    Store.organization_id == org_id,
                    Store.connected == True
                )
            )
            stores = list(result.scalars().all())
            if not stores:
                return IngestionResult(
                    success=False,
                    message="Aucune boutique connectée à synchroniser.",
                    platform="omnichannel",
                    products_count=0,
                    sales_logs_count=0
                )

        total_products = 0
        total_sales_logs = 0
        
        shopify_service = ShopifyService(info.context.db)
        forecasting = ForecastingService(info.context.db)
        alerts = AlertService(info.context.db)

        for store in stores:
            # 2. Synchronisation
            res = await shopify_service.trigger_mock_sync(str(store.id), platform=store.platform.value)
            
            # Mise à jour metadata
            store.last_sync_at = datetime.utcnow()
            store.health_status = "HEALTHY"

            # 3. Pipeline IA & Alerts
            clean_res = await forecasting.run_cleaning_pipeline(str(store.id))
            if clean_res.success:
                await forecasting.run_prediction_pipeline(str(store.id))
                await alerts.check_for_stockouts(str(store.id))
            else:
                logger.warning(f"[OmnichannelSync] Cleaning failed for {store.platform.value}: {clean_res.message}")
            
            total_products += res.products_created
            total_sales_logs += res.sales_logs_created

        await info.context.db.commit()

        return IngestionResult(
            success=True,
            message=f"Sync Omnicanale réussie ({len(stores)} boutiques impactées).",
            platform="omnichannel",
            products_count=total_products,
            sales_logs_count=total_sales_logs,
        )
