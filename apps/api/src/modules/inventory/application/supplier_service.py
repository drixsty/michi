"""
SupplierService — Gestion de la performance fournisseurs (Sprint 8).
Calcul des scores de fiabilité et délais moyens basés sur les PurchaseOrders.
Design Hexagonal (Dépend des Ports).
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from loguru import logger

from modules.inventory.domain.entities import SupplierEntity, PurchaseOrderEntity
from modules.inventory.domain.ports import ISupplierRepository, IPurchaseOrderRepository

class SupplierService:
    def __init__(
        self, 
        supplier_repo: ISupplierRepository,
        po_repo: IPurchaseOrderRepository
    ):
        self.supplier_repo = supplier_repo
        self.po_repo = po_repo

    async def get_suppliers(self, store_id: UUID) -> List[SupplierEntity]:
        """Liste tous les fournisseurs d'un magasin."""
        return await self.supplier_repo.list_by_store(store_id)

    async def update_supplier_performance(self, supplier_id: UUID) -> Optional[SupplierEntity]:
        """
        Recalcule les métriques de performance d'un fournisseur.
        Fiabilité = % de commandes reçues à temps.
        Délai moyen = moy(date_réelle - date_prévue).
        """
        logger.info(f"[SupplierService] Updating performance for supplier {supplier_id}")
        
        # 1. Récupérer toutes les commandes reçues
        orders = await self.po_repo.list_by_supplier(supplier_id, status="RECEIVED")

        if not orders:
            logger.info(f"[SupplierService] No received orders for supplier {supplier_id}")
            return None

        total = len(orders)
        on_time = 0
        total_delay = 0

        for order in orders:
            if not order.actual_arrival_date:
                continue
                
            # Écart en jours (positif = retard)
            delay = (order.actual_arrival_date - order.expected_arrival_date).days
            total_delay += max(0, delay)
            
            if delay <= 0:
                on_time += 1

        # 2. Récupérer l'entité
        supplier = await self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            return None
            
        # 3. Mettre à jour les scores (Calcul métier)
        from dataclasses import replace
        updated_supplier = replace(
            supplier,
            reliability_score=on_time / total,
            average_delay_days=total_delay / total
        )
        
        # 4. Sauvegarder
        return await self.supplier_repo.save(updated_supplier)

    async def get_supplier_by_id(self, supplier_id: UUID) -> Optional[SupplierEntity]:
        return await self.supplier_repo.get_by_id(supplier_id)
