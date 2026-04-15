from core.database.models import Organization, User, OrganizationMember
"""
Inventory Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""
import csv
import strawberry
from typing import List, Optional, Annotated
import uuid

from core.exceptions import UnauthenticatedException, MichiException, ErrorCode
from modules.auth.adapters.decorators import require_permission
from modules.auth.domain.constants import MichiPermission
from core.graphql.types import (
    ProductType, AlertType, SupplierType, StoreType,
    PurchaseOrderType, OmnichannelProductType,
    IngestionResult
)

# Helper functions for ProductType field resolvers
async def resolve_product_channels(info, sku: str):
    service = info.context.services.omnichannel_service
    
    org_id = info.context.org_id
    if not org_id: return []
    
    # Delegate to Service
    from core.graphql.types import ChannelBreakdownType
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
    service = info.context.services.inventory_service
    s = await service.supplier_repo.get_by_id(uuid.UUID(supplier_id))
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

        from loguru import logger
        logger.debug(f"[Inventory] Querying products store_id={store_id}, id={id}, org_id={info.context.org_id}")
        
        items = await service.get_products(shop_ids, product_id=str(id) if id else None)
        logger.debug(f"[Inventory] Found {len(items)} products")
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
        res = await service.alert_repo.mark_as_read(uuid.UUID(str(alert_id)))
        await info.context.db.commit()
        return res

    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_EDIT)
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
        service = info.context.services.inventory_service
        
        # Prepare kwargs for update_settings
        updates = {}
        if lead_time is not None: updates["lead_time"] = lead_time
        if moq is not None: updates["moq"] = moq
        if boost_factor is not None: updates["boost_factor"] = boost_factor
        if stock_weight is not None: updates["stock_weight"] = stock_weight
        if cost_price is not None: updates["cost_price"] = cost_price
        if sale_price is not None: updates["sale_price"] = sale_price

        updated_p = await service.update_product_settings(str(id), **updates)
        await info.context.db.commit()
        return ProductType.from_db(updated_p)

    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_EDIT)
    async def delete_alert(self, info, alert_id: strawberry.ID) -> bool:
        service = info.context.services.alert_service
        res = await service.alert_repo.delete(uuid.UUID(str(alert_id)))
        await info.context.db.commit()
        return res

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
        await info.context.db.commit()
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
        from modules.ingestion.application.service import IngestionService
        ingestion_service = IngestionService(info.context.db)
        from modules.ingestion.connectors.csv import CSVConnector
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
        
        await info.context.db.commit()
        
        return IngestionResult(
            success=True, 
            message="Import CSV réussi.", 
            platform="csv", 
            products_count=result["products_count"], 
            sales_logs_count=result["sales_logs_count"]
        )
