from strawberry.dataloader import DataLoader
import uuid
from typing import List, Optional
from sqlalchemy import select
from modules.inventory.infrastructure.persistence.models import Store, Supplier

def create_store_loader(db) -> DataLoader[uuid.UUID, Optional[Store]]:
    async def load_stores(keys: List[uuid.UUID]) -> List[Optional[Store]]:
        if not keys:
            return []
        
        # Convert keys to UUID to ensure compatibility
        uuid_keys = [uuid.UUID(str(key)) for key in keys]
        
        stmt = select(Store).where(Store.id.in_(uuid_keys))
        result = await db.execute(stmt)
        stores = result.scalars().all()
        
        # Map by both uuid.UUID and str to ensure safe lookups
        store_map = {store.id: store for store in stores}
        return [store_map.get(uuid.UUID(str(key))) for key in keys]
        
    return DataLoader(load_fn=load_stores)

def create_supplier_loader(db) -> DataLoader[uuid.UUID, Optional[Supplier]]:
    async def load_suppliers(keys: List[uuid.UUID]) -> List[Optional[Supplier]]:
        if not keys:
            return []
            
        uuid_keys = [uuid.UUID(str(key)) for key in keys]
        
        stmt = select(Supplier).where(Supplier.id.in_(uuid_keys))
        result = await db.execute(stmt)
        suppliers = result.scalars().all()
        
        supplier_map = {supplier.id: supplier for supplier in suppliers}
        return [supplier_map.get(uuid.UUID(str(key))) for key in keys]
        
    return DataLoader(load_fn=load_suppliers)
