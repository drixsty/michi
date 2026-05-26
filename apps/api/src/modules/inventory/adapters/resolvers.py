from core.database.models import Organization, User, OrganizationMember
"""
Inventory Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""

_MAX_PAGE_SIZE = 500  # plafond absolu pour éviter les requêtes abusives
import csv
import strawberry
from typing import List, Optional, Annotated, Any
import uuid
import asyncio
import time

from core.exceptions import UnauthenticatedException, MichiException, ErrorCode
from modules.auth.adapters.decorators import require_permission, require_plan
from core.security.plans import PlanName
from modules.auth.domain.constants import MichiPermission
from core.graphql.types import (
    ProductType, AlertType, SupplierType, StoreType,
    PurchaseOrderType, OmnichannelProductType,
    IngestionResult, CsvAnalysisType, MappingSuggestionType,
    SmartImportInput, UpdateCredentialInput, CredentialType, TestConnectionResult
)

# Helper functions for ProductType field resolvers
async def resolve_product_channels(info: strawberry.types.Info, sku: str):
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

async def resolve_product_supplier(info: strawberry.types.Info, supplier_id: str):
    service = info.context.services.inventory_service
    s = await service.supplier_repo.get_by_id(uuid.UUID(supplier_id))
    return SupplierType.from_db(s)

@strawberry.type
class InventoryQuery:
    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def products(
        self,
        info: strawberry.types.Info,
        store_id: Optional[strawberry.ID] = None,
        id: Optional[strawberry.ID] = None,
        title: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
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
        logger.debug(f"[Inventory] Querying products store_id={store_id}, id={id}, title={title}, org_id={info.context.org_id}")
        
        capped_limit = min(max(1, limit), _MAX_PAGE_SIZE)
        items = await service.get_products(shop_ids, product_id=str(id) if id else None, search=title)
        logger.debug(f"[Inventory] Found {len(items)} products (limit={capped_limit}, offset={offset})")
        return [ProductType.from_db(p) for p in items[offset: offset + capped_limit]]

    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def suppliers(
        self, 
        info: strawberry.types.Info, 
        store_id: Optional[strawberry.ID] = None, 
        name: Optional[str] = None
    ) -> List[SupplierType]:
        service = info.context.services.inventory_service
        
        if store_id:
            shop_ids = [str(store_id)]
        else:
            org_id = info.context.org_id
            if not org_id: return []
            stores = await service.store_repo.list_by_organization(uuid.UUID(str(org_id)))
            shop_ids = [str(s.id) for s in stores]
            
        items = await service.get_suppliers(shop_ids, search=name)
        return [SupplierType.from_db(s) for s in items]

    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def unread_alerts(self, info: strawberry.types.Info, store_id: Optional[strawberry.ID] = None) -> List[AlertType]:
        service = info.context.services.alert_service
        alerts = await service.get_unread_alerts(
            store_id=str(store_id) if store_id else None,
            organization_id=str(info.context.org_id) if not store_id else None
        )
        return [AlertType.from_db(a) for a in alerts]

    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def sources(self, info: strawberry.types.Info) -> List[StoreType]:
        """Retourne les stores de l'organisation active."""
        if not info.context.user_id or not info.context.org_id:
            return []
        
        service = info.context.services.inventory_service
        stores = await service.store_repo.list_by_organization(uuid.UUID(str(info.context.org_id)))
        return [StoreType.from_db(s) for s in stores]

    @strawberry.field
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def omnichannel_inventory(self, info: strawberry.types.Info) -> List[OmnichannelProductType]:
        service = info.context.services.omnichannel_service
        items = await service.get_omnichannel_inventory(str(info.context.org_id))
        return [OmnichannelProductType.from_dto(item) for item in items]

@strawberry.type
class InventoryMutation:
    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_EDIT)
    async def mark_alert_as_read(self, info: strawberry.types.Info, alert_id: strawberry.ID) -> bool:
        service = info.context.services.alert_service
        res = await service.alert_repo.mark_as_read(uuid.UUID(str(alert_id)))
        await info.context.db.commit()
        return res

    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_EDIT)
    async def update_product_settings(
        self,
        info: strawberry.types.Info,
        id: strawberry.ID,
        lead_time: Optional[int] = None,
        moq: Optional[int] = None,
        boost_factor: Optional[float] = None,
        stock_weight: Optional[float] = None,
        cost_price: Optional[float] = None,
        sale_price: Optional[float] = None,
        supplier_id: Optional[strawberry.ID] = None
    ) -> ProductType:
        service = info.context.services.inventory_service
        
        # Prepare kwargs for update_settings
        updates: dict[str, Any] = {}
        if lead_time is not None: updates["lead_time"] = lead_time
        if moq is not None: updates["moq"] = moq
        if boost_factor is not None: updates["boost_factor"] = boost_factor
        if stock_weight is not None: updates["stock_weight"] = stock_weight
        if cost_price is not None: updates["cost_price"] = cost_price
        if sale_price is not None: updates["sale_price"] = sale_price
        if supplier_id is not None:
            if not supplier_id or str(supplier_id).lower() in ("null", "none"):
                updates["supplier_id"] = None
            else:
                updates["supplier_id"] = uuid.UUID(str(supplier_id))

        updated_p = await service.update_product_settings(str(id), **updates)
        await info.context.db.commit()
        return ProductType.from_db(updated_p)

    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_VIEW)
    async def delete_alert(self, info: strawberry.types.Info, alert_id: strawberry.ID) -> bool:
        service = info.context.services.alert_service
        res = await service.alert_repo.delete(uuid.UUID(str(alert_id)))
        await info.context.db.commit()
        return res

    @strawberry.mutation(name="toggleSource")
    @require_permission(MichiPermission.STORES_MANAGE)
    async def toggle_source(
        self, 
        info: strawberry.types.Info, 
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
        info: strawberry.types.Info, 
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
    @strawberry.mutation
    @require_permission(MichiPermission.STORES_MANAGE)
    async def analyze_csv(self, info: strawberry.types.Info, csv_content: str) -> CsvAnalysisType:
        """Analyse la structure du CSV ou Excel et suggère un mapping."""
        from modules.ingestion.connectors.csv import CSVConnector
        import json
        import base64
        
        is_excel = False
        final_content = csv_content
        
        # Détection Base64 (Data URL) pour Excel
        if csv_content.startswith("data:"):
            try:
                # Format: data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,....
                header, base64_data = csv_content.split(",", 1)
                final_content = base64.b64decode(base64_data)
                is_excel = "spreadsheet" in header or "excel" in header
            except:
                pass

        connector = CSVConnector()
        analysis = await connector.discover_schema(final_content, is_excel=is_excel)
        
        # Transformer le mapping suggéré en liste de MappingSuggestionType
        suggestions = []
        for target, col in analysis["suggested_mapping"].items():
            suggestions.append(MappingSuggestionType(
                target_field=target,
                csv_column=col,
                confidence=0.9 # Valeur par défaut pour le MVP
            ))
            
        # Résumé d'impact
        impact = analysis.get("impact", {})
        impact_msg = f"Fichier {'Excel' if impact.get('is_excel') else 'CSV'} analysé. "
        impact_msg += f"{impact.get('total_rows')} lignes de données trouvées. "
        impact_msg += f"{impact.get('unique_skus')} produits uniques identifiés."
            
        return CsvAnalysisType(
            columns=analysis["columns"],
            column_types=json.dumps(analysis["column_types"]),
            suggested_mapping=suggestions,
            sample_data=json.dumps(analysis["sample_data"]),
            anomalies=json.dumps(analysis.get("anomalies", [])),
            impact_summary=impact_msg
        )

    @strawberry.mutation
    @require_permission(MichiPermission.STORES_MANAGE)
    @require_plan(PlanName.PRO)
    async def update_store_credentials(self, info: strawberry.types.Info, input: UpdateCredentialInput) -> CredentialType:
        """Met à jour les credentials chiffrés d'un store."""
        import json
        from modules.inventory.infrastructure.repositories.credential_repository import SQLAlchemyCredentialRepository
        from modules.inventory.domain.entities import CredentialEntity
        
        db = info.context.db
        repo = SQLAlchemyCredentialRepository(db)
        
        # Préparer l'entité
        meta = json.loads(input.meta_json or "{}")
        entity = CredentialEntity(
            id=uuid.uuid4(),
            store_id=uuid.UUID(str(input.store_id)),
            access_token=input.access_token,
            api_key=input.api_key,
            api_secret=input.api_secret,
            meta=meta
        )
        
        saved = await repo.save(entity)
        await db.commit()
        
        return CredentialType(
            id=strawberry.ID(str(saved.id)),
            store_id=strawberry.ID(str(saved.store_id)),
            api_key_last_chars=saved.api_key[-4:] if saved.api_key else None,
            has_token=bool(saved.access_token),
            meta=json.dumps(saved.meta),
            updated_at=saved.updated_at
        )

    @strawberry.mutation
    @require_permission(MichiPermission.STORES_MANAGE)
    async def test_store_connection(self, info: strawberry.types.Info, store_id: strawberry.ID) -> TestConnectionResult:
        """Teste la connexion d'un store avec ses credentials enregistrés."""
        import time
        from modules.inventory.infrastructure.repositories.credential_repository import SQLAlchemyCredentialRepository
        
        db = info.context.db
        repo = SQLAlchemyCredentialRepository(db)
        
        credentials = await repo.get_by_store(uuid.UUID(str(store_id)))
        if not credentials:
            return TestConnectionResult(success=False, message="Aucun credential trouvé pour ce store.")
        
        # Simulation de test (en attendant l'implémentation réelle par plateforme)
        start = time.time()
        await asyncio.sleep(0.5) # Simuler un appel réseau
        latency = int((time.time() - start) * 1000)
        
        return TestConnectionResult(
            success=True, 
            message="Connexion réussie (Simulation)", 
            latency_ms=latency
        )

    @strawberry.mutation
    @require_permission(MichiPermission.STORES_MANAGE)
    async def smart_import(self, info: strawberry.types.Info, info_input: SmartImportInput) -> IngestionResult:
        """Exécute l'importation avec le mapping validé par l'utilisateur."""
        import json
        from core.exceptions import DomainValidationError
        
        service = info.context.services.inventory_service
        
        try:
            mapping = json.loads(info_input.mapping)
        except json.JSONDecodeError:
            raise DomainValidationError("Mapping JSON invalide.")
        
        from modules.ingestion.application.service import IngestionService
        ingestion_service = IngestionService(info.context.db, inventory_service=service, alert_service=info.context.services.alert_service)
        from modules.ingestion.connectors.csv import CSVConnector
        ingestion_service.register_connector("csv", CSVConnector())

        import base64
        is_excel = False
        final_content = info_input.csv_content
        
        if info_input.csv_content.startswith("data:"):
            try:
                header, base64_data = info_input.csv_content.split(",", 1)
                final_content = base64.b64decode(base64_data)
                is_excel = "spreadsheet" in header or "excel" in header
            except Exception as e:
                raise DomainValidationError(f"Fichier corrompu ou format Base64 invalide : {str(e)}")

        result = await service.ingest_csv_orchestrator(
            store_id=str(info_input.store_id),
            csv_content=final_content,
            mapping=mapping,
            ingestion_service=ingestion_service,
            forecasting_service=info.context.services.forecasting_service,
            alert_service=info.context.services.alert_service,
            organization_id=info.context.org_id,
            is_excel=is_excel
        )
        
        await info.context.db.commit()
        
        return IngestionResult(
            success=True, 
            message="Importation intelligente réussie.", 
            platform="csv", 
            products_count=result["products_count"], 
            sales_logs_count=result["sales_logs_count"]
        )

    @strawberry.mutation
    @require_permission(MichiPermission.INVENTORY_EDIT)
    async def create_purchase_order(
        self, 
        info: strawberry.types.Info, 
        product_id: strawberry.ID, 
        supplier_id: strawberry.ID, 
        quantity: int
    ) -> PurchaseOrderType:
        """Crée un bon de commande fournisseur."""
        service = info.context.services.inventory_service
        po = await service.create_purchase_order(
            product_id=uuid.UUID(str(product_id)),
            supplier_id=uuid.UUID(str(supplier_id)),
            quantity=quantity
        )
        await info.context.db.commit()
        return PurchaseOrderType.from_db(po)
