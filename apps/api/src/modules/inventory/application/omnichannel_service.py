from core.database.models import Organization, User, OrganizationMember
"""
OmnichannelService — Application Layer
Aggregates inventory by SKU across channels.
"""
from typing import List, Optional, Dict
from datetime import date
from uuid import UUID

from modules.inventory.domain.ports import IProductRepository, IStoreRepository

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

from modules.forecasting.domain.ports import IPredictionRepository

class OmnichannelService:
    def __init__(
        self, 
        product_repo: IProductRepository, 
        store_repo: IStoreRepository,
        prediction_repo: IPredictionRepository
    ):
        self.product_repo = product_repo
        self.store_repo = store_repo
        self.prediction_repo = prediction_repo

    async def get_omnichannel_inventory(self, org_id: str) -> List[OmnichannelProduct]:
        """
        Retourne la vue omnichannel de l'inventaire — agrégation par SKU avec prédictions.
        """
        o_uuid = UUID(org_id)

        # 1. Charger les stores de l'organisation
        active_stores = await self.store_repo.list_by_organization(o_uuid, connected_only=True)
        active_store_ids = [s.id for s in active_stores]

        if not active_store_ids:
            return []

        # 2. Charger les produits et les prédictions
        products = await self.product_repo.list_by_store(active_store_ids)
        if not products:
            return []

        # Charger toutes les prédictions pour l'organisation pour éviter le N+1
        predictions = await self.prediction_repo.list_by_organization(o_uuid)
        prediction_map = {p.product_id: p for p in predictions}

        # 3. Agréger par SKU
        sku_map: Dict[str, OmnichannelProduct] = {}

        for product in products:
            sku = product.sku
            if sku not in sku_map:
                sku_map[sku] = OmnichannelProduct(
                    sku=sku,
                    title=product.title,
                    total_stock=0,
                    channels=[],
                )
            
            omni = sku_map[sku]
            pred = prediction_map.get(product.id)
            
            # Mapping entity to breakdown
            channel = ChannelStockBreakdown(
                platform=product.source_platform.value,
                product_id=str(product.id),
                current_stock=product.current_stock,
                lead_time=product.lead_time,
                moq=product.moq,
                run_rate=pred.run_rate if pred else 0.0,
                stock_weight=product.stock_weight
            )
            omni.channels.append(channel)
            omni.total_stock += product.current_stock
            omni.channel_count = len(omni.channels)
            
            # Agrégation des KPIs (on prend le plus pessimiste/critique pour le SKU)
            if pred:
                omni.dominant_run_rate += pred.run_rate
                omni.total_reorder_quantity += pred.reorder_quantity
                omni.annual_gross_profit += pred.annual_gross_profit
                
                # ABC Rank: on prend le meilleur (A > B > C)
                if pred.abc_rank and (not omni.abc_rank or pred.abc_rank < omni.abc_rank):
                    omni.abc_rank = pred.abc_rank
                
                # Stockout Date: la plus proche
                if pred.predicted_stockout_date:
                    if not omni.predicted_stockout_date or pred.predicted_stockout_date < omni.predicted_stockout_date:
                        omni.predicted_stockout_date = pred.predicted_stockout_date

        # 4. Sort and return
        result_list = sorted(
            sku_map.values(),
            key=lambda x: (not x.has_conflict, x.total_stock),
        )

        return result_list

    async def get_channels_for_sku(self, sku: str, org_id: str) -> List[ChannelStockBreakdown]:
        """
        Retourne le détail des canaux pour un SKU spécifique dans une organisation.
        Utile pour les résolveurs ProductType.channels.
        """
        o_uuid = UUID(org_id)
        
        # 1. Charger les stores de l'organisation
        active_stores = await self.store_repo.list_by_organization(o_uuid, connected_only=True)
        active_store_ids = [s.id for s in active_stores]
        
        if not active_store_ids:
            return []
            
        # 2. Charger les produits pour ce SKU dans ces stores
        products = await self.product_repo.list_by_store(active_store_ids)
        sku_products = [p for p in products if p.sku == sku]
        
        breakdown = []
        for product in sku_products:
            breakdown.append(ChannelStockBreakdown(
                platform=product.source_platform.value,
                product_id=str(product.id),
                current_stock=product.current_stock,
                lead_time=product.lead_time,
                moq=product.moq,
                run_rate=0.0, # Filled via resolver if needed
                stock_weight=product.stock_weight
            ))
            
        return breakdown
