import strawberry
from typing import List, Optional
from datetime import datetime
import uuid

from src.core.exceptions import UnauthenticatedException
from .service import InventoryService
from .alert_service import AlertService
from .models import PlatformSource

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
class IngestionResult:
    success: bool
    message: str
    platform: str
    products_count: int
    sales_logs_count: int

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
