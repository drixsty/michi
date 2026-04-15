"""
OmnichannelService — Application Layer
Aggregates inventory by SKU across channels.
"""
from typing import List, Optional, Dict
from datetime import date
from uuid import UUID

from src.modules.inventory.domain.ports import IProductRepository, IStoreRepository

# We keep the dataclasses here as they are Application-specific DTOs for the UI
from dataclasses import dataclass, field

@dataclass
class ChannelStockBreakdown:
    platform: str
    product_id: str
    current_stock: int
    lead_time: int
    moq: int
    run_rate: float
    stock_weight: float

@dataclass
class OmnichannelProduct:
    sku: str
    title: str
    total_stock: int
    channels: List[ChannelStockBreakdown] = field(default_factory=list)
    channel_count: int = 0
    has_conflict: bool = False
    predicted_stockout_date: Optional[date] = None
    total_reorder_quantity: int = 0
    dominant_run_rate: float = 0.0
    abc_rank: str = 'C'
    annual_gross_profit: float = 0.0

class OmnichannelService:
    def __init__(self, product_repo: IProductRepository, store_repo: IStoreRepository):
        self.product_repo = product_repo
        self.store_repo = store_repo

    async def get_omnichannel_inventory(self, org_id: str) -> List[OmnichannelProduct]:
        """
        Retourne la vue omnichannel de l'inventaire — agrégation par SKU.
        """
        o_uuid = UUID(org_id)

        # 1. Charger les stores de l'organisation
        active_stores = await self.store_repo.list_by_organization(o_uuid, connected_only=True)
        active_store_ids = [s.id for s in active_stores]

        if not active_store_ids:
            return []

        # 2. Charger les produits via le repository
        products = await self.product_repo.list_by_store(active_store_ids)
        if not products:
            return []

        # 3. Agréger par SKU (logic unchanged from original service, just using entities)
        sku_map: Dict[str, OmnichannelProduct] = {}

        for product in products:
            sku = product.sku
            # Note: For now, we assume predictions are pre-loaded or 
            # we'll need IForecastingRepository in the future.
            
            # Simplified aggregation logic (reusing standard logic)
            if sku not in sku_map:
                sku_map[sku] = OmnichannelProduct(
                    sku=sku,
                    title=product.title,
                    total_stock=0,
                    channels=[],
                )
            
            omni = sku_map[sku]
            # Mapping entity to breakdown
            channel = ChannelStockBreakdown(
                platform=product.source_platform.value,
                product_id=str(product.id),
                current_stock=product.current_stock,
                lead_time=product.lead_time,
                moq=product.moq,
                run_rate=0.0, # Will be filled from Forecasting module later
                stock_weight=product.stock_weight
            )
            omni.channels.append(channel)
            omni.total_stock += product.current_stock
            omni.channel_count = len(omni.channels)

        # 4. Sort and return
        result_list = sorted(
            sku_map.values(),
            key=lambda x: (not x.has_conflict, x.total_stock),
        )

        return result_list
