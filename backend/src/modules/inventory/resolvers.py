import csv
import io
import strawberry
from typing import List, Optional
from datetime import datetime
import uuid

from src.core.exceptions import UnauthenticatedException
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
    title: str
    sku: str
    lead_time: int
    moq: int
    current_stock: int
    boost_factor: float
    stock_weight: float
    cost_price: Optional[float]
    sale_price: Optional[float]

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
    channels: List[ChannelBreakdownType]


@strawberry.type
class InventoryQuery:
    @strawberry.field
    async def unread_alerts(self, info) -> List[AlertType]:
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        # On suppose que l'utilisateur n'a qu'un shop pour le MVP
        # Dans une vraie app, on prendrait shop_id du shop de l'utilisateur
        from src.modules.auth.service import AuthService
        auth_service = AuthService(info.context.db)
        user = await auth_service.get_user_by_id(info.context.user_id)
        
        alert_service = AlertService(info.context.db)
        alerts = await alert_service.get_unread_alerts(user.shop_id)
        
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
    async def suppliers(self, info) -> List[SupplierType]:
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        from src.modules.auth.service import AuthService
        auth_service = AuthService(info.context.db)
        user = await auth_service.get_user_by_id(info.context.user_id)
        
        service = SupplierService(info.context.db)
        suppliers = await service.get_suppliers(user.shop_id)
        
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
        """
        Vue agrégée de l'inventaire par SKU toutes plateformes (US 9.1 / Sprint 9).

        Regroupe les produits par SKU et consolide les stocks Shopify,
        WooCommerce, Amazon, CSV en une seule ligne par référence.

        Retourne les SKUs triés par risque (conflits cross-canal en premier,
        puis stock croissant).

        Example:
            query {
              omnichannelInventory {
                sku title totalStock channelCount hasConflict
                dominantRunRate totalReorderQuantity predictedStockoutDate
                channels { platform currentStock leadTime }
              }
            }
        """
        if not info.context.user_id:
            raise UnauthenticatedException()

        from src.modules.auth.service import AuthService
        user = await AuthService(info.context.db).get_user_by_id(info.context.user_id)

        service = OmnichannelService(info.context.db)
        items = await service.get_omnichannel_inventory(str(user.shop_id))

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
    async def export_replenishment_csv(self, info) -> str:
        """
        Génère le CSV de réapprovisionnement (US 9.4 / Sprint 9).

        Retourne une chaîne CSV contenant :
            SKU, Titre, Plateforme, Stock actuel, Run rate, Jours de stock,
            Date rupture prévisionnelle, Quantité à commander, Lead time, MOQ

        Trié par date de rupture la plus proche.

        Le frontend déclenche le téléchargement directement depuis cette string.

        Example:
            query {
              exportReplenishmentCsv
            }
        """
        if not info.context.user_id:
            raise UnauthenticatedException()

        from src.modules.auth.service import AuthService
        user = await AuthService(info.context.db).get_user_by_id(info.context.user_id)

        service = OmnichannelService(info.context.db)
        rows = await service.get_replenishment_export_data(str(user.shop_id))

        # Générer le CSV en mémoire
        output = io.StringIO()
        fieldnames = [
            "sku", "title", "platform", "current_stock", "run_rate",
            "days_of_stock", "predicted_stockout_date", "reorder_quantity",
            "lead_time", "moq",
        ]
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
        csv_content: str, 
        sku_col: str = "sku",
        date_col: str = "date",
        sales_col: str = "sales",
        stock_col: str = "stock",
        title_col: str = "title"
    ) -> IngestionResult:
        if not info.context.user_id:
            raise UnauthenticatedException()

        from src.modules.auth.service import AuthService
        auth_service = AuthService(info.context.db)
        user = await auth_service.get_user_by_id(info.context.user_id)

        from src.modules.ingestion.service import IngestionService
        from src.modules.ingestion.connectors.csv import CSVConnector
        
        ingestion_service = IngestionService(info.context.db)
        ingestion_service.register_connector("csv", CSVConnector())
        
        mapping = {
            "sku": sku_col,
            "date": date_col,
            "units_sold": sales_col,
            "stock": stock_col,
            "title": title_col
        }
        
        result = await ingestion_service.ingest_from_platform(
            platform="csv",
            shop_id=str(user.shop_id),
            csv_content=csv_content,
            mapping=mapping
        )
        
        # Déclencher le nettoyage et les prédictions (Simplifié ici pour le MVP)
        from src.modules.forecasting.service import ForecastingService
        forecasting_service = ForecastingService(info.context.db)
        await forecasting_service.run_cleaning_pipeline(user.shop_id)
        await forecasting_service.run_prediction_pipeline(user.shop_id)
        
        # Déclencher les alertes
        from .alert_service import AlertService
        alert_service = AlertService(info.context.db)
        await alert_service.check_for_stockouts(user.shop_id)

        return IngestionResult(
            success=True,
            message="Import CSV réussi et alertes calculées.",
            platform="csv",
            products_count=result["products_count"],
            sales_logs_count=result["sales_logs_count"]
        )

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
    async def create_purchase_order(
        self, 
        info, 
        product_id: strawberry.ID, 
        supplier_id: strawberry.ID, 
        quantity: int,
        expected_days: int = 14
    ) -> PurchaseOrderType:
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        from src.modules.auth.service import AuthService
        auth_service = AuthService(info.context.db)
        user = await auth_service.get_user_by_id(info.context.user_id)
        
        from .models import (
            Product, 
            SalesLog, 
            Supplier, 
            Alert, 
            PurchaseOrder, 
            PlatformSource
        )
        from datetime import date, timedelta
        
        po = PurchaseOrder(
            shop_id=user.shop_id,
            product_id=uuid.UUID(str(product_id)),
            supplier_id=uuid.UUID(str(supplier_id)),
            quantity=quantity,
            expected_arrival_date=date.today() + timedelta(days=expected_days),
            status="PENDING"
        )
        info.context.db.add(po)
        await info.context.db.flush()

        # Envoi de la notification email (Sprint 16)
        try:
            from .email_service import EmailService
            from sqlalchemy import select
            
            # Récupérer les détails pour l'email
            prod_res = await info.context.db.execute(select(Product).where(Product.id == po.product_id))
            product = prod_res.scalar_one()
            
            supp_res = await info.context.db.execute(select(Supplier).where(Supplier.id == po.supplier_id))
            supplier = supp_res.scalar_one()

            if supplier.contact_email:
                email_service = EmailService()
                await email_service.send_purchase_order(
                    to_email=supplier.contact_email,
                    po_id=str(po.id),
                    supplier_name=supplier.name,
                    product_title=product.title,
                    product_sku=product.sku,
                    quantity=po.quantity,
                    order_date=str(po.order_date),
                    expected_date=str(po.expected_arrival_date)
                )
        except Exception as e:
            from loguru import logger
            logger.error(f"[PurchaseOrder] Failed to trigger notification email: {str(e)}")
        
        return PurchaseOrderType(
            id=strawberry.ID(str(po.id)),
            product_id=strawberry.ID(str(po.product_id)),
            supplier_id=strawberry.ID(str(po.supplier_id)),
            quantity=po.quantity,
            order_date=str(po.order_date),
            expected_arrival_date=str(po.expected_arrival_date),
            actual_arrival_date=None,
            status=po.status
        )

    @strawberry.mutation
    async def ingest_woocommerce_data(
        self,
        info,
        products_csv: str,
        orders_csv: str = "",
    ) -> IngestionResult:
        """
        Importe les données depuis un export WooCommerce natif (US 9.2 / Sprint 9).

        Args:
            products_csv : Contenu du fichier CSV Products WooCommerce.
            orders_csv   : Contenu du fichier CSV Orders WooCommerce (optionnel).
                           Si vide, seul le stock actuel est importé.

        Example:
            mutation {
              ingestWoocommerceData(
                productsCsv: "SKU,Name,Stock\\nROBE-S,Robe noire S,12"
                ordersCsv: "SKU,Date,Quantity,Status\\nROBE-S,2025-01-15,2,completed"
              ) {
                success message productsCount salesLogsCount
              }
            }
        """
        if not info.context.user_id:
            raise UnauthenticatedException()

        from src.modules.auth.service import AuthService
        from .models import PlatformSource
        auth_service = AuthService(info.context.db)
        user = await auth_service.get_user_by_id(info.context.user_id)

        from src.modules.ingestion.service import IngestionService
        from src.modules.ingestion.connectors.woocommerce import WooCommerceConnector

        ingestion_service = IngestionService(info.context.db)
        ingestion_service.register_connector("woocommerce", WooCommerceConnector())

        result = await ingestion_service.ingest_from_platform(
            platform="woocommerce",
            shop_id=str(user.shop_id),
            csv_content=products_csv,
            orders_csv=orders_csv or None,
            mapping={},
            source_platform=PlatformSource.WOOCOMMERCE,
        )

        # Pipeline IA auto-déclenchée après ingestion
        from src.modules.forecasting.service import ForecastingService
        forecasting_service = ForecastingService(info.context.db)
        await forecasting_service.run_cleaning_pipeline(str(user.shop_id))
        await forecasting_service.run_prediction_pipeline(str(user.shop_id))

        from .alert_service import AlertService as _AlertService
        await _AlertService(info.context.db).check_for_stockouts(str(user.shop_id))

        return IngestionResult(
            success=True,
            message=f"Import WooCommerce réussi — {result.get('products_count', 0)} produits.",
            platform="woocommerce",
            products_count=result.get("products_count", 0),
            sales_logs_count=result.get("sales_logs_count", 0),
        )

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

    @strawberry.mutation
    async def trigger_omnichannel_sync(self, info) -> IngestionResult:
        """
        Déclenche la synchronisation de TOUTES les sources connectées (Sprint 17).
        Remplace l'ancienne version statique par une version basée sur la base de données.
        """
        if not info.context.user_id:
            raise UnauthenticatedException()

        from src.modules.auth.service import AuthService
        from src.modules.inventory.models import SourceConnection, PlatformSource
        from src.modules.shopify.service import ShopifyService # Mock for now
        from src.modules.forecasting.service import ForecastingService
        from .alert_service import AlertService
        from sqlalchemy import select
        from datetime import datetime
        
        auth_service = AuthService(info.context.db)
        user = await auth_service.get_user_by_id(info.context.user_id)
        shop_id = str(user.shop_id)

        # 1. Identifier les sources actives
        result = await info.context.db.execute(
            select(SourceConnection).where(
                SourceConnection.shop_id == user.shop_id,
                SourceConnection.connected == True
            )
        )
        active_connections = result.scalars().all()
        
        if not active_connections:
            return IngestionResult(
                success=False,
                message="Aucune source connectée. Connectez une boutique d'abord.",
                platform="none",
                products_count=0,
                sales_logs_count=0
            )

        total_prods = 0
        total_logs = 0
        platforms_synced = []

        # 2. Synchronisation séquentielle (Mocking logic for multi-channel)
        shopify_service = ShopifyService(info.context.db)
        
        for conn in active_connections:
            # Simulation : On utilise le mock generator pour toutes les sources connectées
            # En production, chaque plateforme appellerait son propre service
            res = await shopify_service.trigger_mock_sync(shop_id, platform=conn.platform.value)
            
            total_prods += res.products_created
            total_logs += res.sales_logs_created
            platforms_synced.append(conn.platform.value)
            
            # Mise à jour metadata
            conn.last_sync_at = datetime.utcnow()
            conn.health_status = "HEALTHY"

        # 3. Pipeline IA Global
        forecasting = ForecastingService(info.context.db)
        await forecasting.run_cleaning_pipeline(shop_id)
        await forecasting.run_prediction_pipeline(shop_id)

        # 4. Alert Pipeline
        alerts = AlertService(info.context.db)
        await alerts.check_for_stockouts(shop_id)

        await info.context.db.commit()

        return IngestionResult(
            success=True,
            message=f"Sync réussie pour : {', '.join(platforms_synced)}.",
            platform="all",
            products_count=total_prods,
            sales_logs_count=total_logs,
        )
