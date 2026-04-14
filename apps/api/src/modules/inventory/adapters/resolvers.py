"""
Inventory Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""
import csv
import io
import strawberry
from typing import List, Optional, Annotated
import uuid
from loguru import logger

from src.core.exceptions import UnauthenticatedException, MichiException, ErrorCode
from src.modules.auth.decorators import require_permission
from src.modules.auth.constants import MichiPermission
from src.core.graphql.types import (
    ProductType, AlertType, SupplierType, StoreType,
    PurchaseOrderType, OmnichannelProductType,
    IngestionResult
)

# Helper functions for ProductType field resolvers
async def resolve_product_channels(info, sku: str):
    from src.modules.inventory.application.omnichannel_service import OmnichannelService
    from src.modules.inventory.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
    from src.modules.inventory.infrastructure.repositories.store_repository import SQLAlchemyStoreRepository
    
    product_repo = SQLAlchemyProductRepository(info.context.db)
    store_repo = SQLAlchemyStoreRepository(info.context.db)
    service = OmnichannelService(product_repo, store_repo)
    
    org_id = info.context.org_id
    if not org_id: return []
    
    # Delegate to Service
    from src.core.graphql.types import ChannelBreakdownType
    channels = await service.get_channels_for_sku(sku, str(org_id))
    return [
        ChannelBreakdownType(
            platform=ch.platform,
            product_id=strawberry.ID(ch.product_id),
            current_stock=ch.current_stock,
            lead_time=ch.lead_time,
            moq=ch.moq,
            run_rate=ch.run_rate,
            stock_weight=ch.stock_weight
        ) for ch in channels
    ]

async def resolve_product_supplier(info, supplier_id: str):
    from src.modules.inventory.infrastructure.repositories.supplier_repository import SQLAlchemySupplierRepository
    repo = SQLAlchemySupplierRepository(info.context.db)
    s = await repo.get_by_id(uuid.UUID(supplier_id))
    return SupplierType.from_db(s)

@strawberry.type
class InventoryQuery:
    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def products(
        self, 
        info, 
        store_id: Optional[strawberry.ID] = None, 
        id: Optional[strawberry.ID] = None
    ) -> List[ProductType]:
        service = info.context.services.inventory_service
        
        # Résolution des shop_ids déléguée ou simplifiée ici
        if store_id:
            shop_ids = [str(store_id)]
        else:
            org_id = info.context.org_id
            if not org_id: return []
            stores = await service.store_repo.list_by_organization(uuid.UUID(str(org_id)))
            shop_ids = [str(s.id) for s in stores]

        items = await service.get_products(shop_ids, product_id=str(id) if id else None)
        return [ProductType.from_db(p) for p in items]

    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def unread_alerts(self, info, store_id: Optional[strawberry.ID] = None) -> List[AlertType]:
        service = info.context.services.alert_service
        alerts = await service.get_unread_alerts(
            store_id=str(store_id) if store_id else None,
            organization_id=str(info.context.org_id) if not store_id else None
        )
        return [AlertType.from_db(a) for a in alerts]

    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def sources(self, info) -> List[StoreType]:
        """Retourne les stores de l'organisation active."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
        
        service = info.context.services.inventory_service
        stores = await service.store_repo.list_by_organization(uuid.UUID(str(info.context.org_id)))
        return [StoreType.from_db(s) for s in stores]

    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def omnichannel_inventory(self, info) -> List[OmnichannelProductType]:
        service = info.context.services.omnichannel_service
        items = await service.get_omnichannel_inventory(str(info.context.org_id))
        return [OmnichannelProductType.from_dto(item) for item in items]

@strawberry.type
class InventoryMutation:
    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_EDIT)
    async def mark_alert_as_read(self, info, alert_id: strawberry.ID) -> bool:
        service = info.context.services.alert_service
        return await service.alert_repo.mark_as_read(uuid.UUID(str(alert_id)))

    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_EDIT)
    async def delete_alert(self, info, alert_id: strawberry.ID) -> bool:
        service = info.context.services.alert_service
        return await service.alert_repo.delete(uuid.UUID(str(alert_id)))

    @strawberry.mutation(name="toggleSource")
    @require_permission(MichiPermission.STORES_MANAGE)
    async def toggle_source(
        self, 
        info, 
        platform: str, 
        connected: bool, 
        store_id: Optional[strawberry.ID] = None
    ) -> StoreType:
        """Gère la connexion/déconnexion d'un Store."""
        service = info.context.services.inventory_service
        saved_store = await service.toggle_source(
            org_id=uuid.UUID(str(info.context.org_id)),
            platform=platform,
            connected=connected,
            store_id=uuid.UUID(str(store_id)) if store_id else None
        )
        return StoreType.from_db(saved_store)

    @strawberry.mutation
    @require_permission(MichiPermission.STORES_MANAGE)
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
        service = info.context.services.inventory_service
        
        # Accès aux autres services via le contexte pour l'orchestrateur
        from src.modules.ingestion.service import IngestionService
        ingestion_service = IngestionService(info.context.db)
        from src.modules.ingestion.connectors.csv import CSVConnector
        ingestion_service.register_connector("csv", CSVConnector())

        mapping = {"sku": sku_col, "date": date_col, "units_sold": sales_col, "stock": stock_col, "title": title_col}
        
        result = await service.ingest_csv_orchestrator(
            store_id=str(store_id),
            csv_content=csv_content,
            mapping=mapping,
            ingestion_service=ingestion_service,
            forecasting_service=info.context.services.forecasting_service,
            alert_service=info.context.services.alert_service
        )
        
        return IngestionResult(
            success=True, 
            message="Import CSV réussi.", 
            platform="csv", 
            products_count=result["products_count"], 
            sales_logs_count=result["sales_logs_count"]
        )
