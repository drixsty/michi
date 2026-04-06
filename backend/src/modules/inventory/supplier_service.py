"""
SupplierService — Gestion de la performance fournisseurs (Sprint 8).
Calcul des scores de fiabilité et délais moyens basés sur les PurchaseOrders.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
from .models import Supplier, PurchaseOrder, Product

class SupplierService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_suppliers(self, shop_id: str):
        """Liste tous les fournisseurs du shop."""
        result = await self.db.execute(
            select(Supplier).where(Supplier.shop_id == shop_id).order_by(Supplier.name)
        )
        return result.scalars().all()

    async def update_supplier_performance(self, supplier_id: str):
        """
        Recalcule les métriques de performance d'un fournisseur.
        Fiabilité = % de commandes reçues à temps.
        Délai moyen = moy(date_réelle - date_prévue).
        """
        # 1. Récupérer toutes les commandes terminées
        result = await self.db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status == "RECEIVED"
            )
        )
        orders = list(result.scalars().all())

        if not orders:
            return

        total = len(orders)
        on_time = 0
        total_delay = 0

        for order in orders:
            # Écart en jours (positif = retard)
            delay = (order.actual_arrival_date - order.expected_arrival_date).days
            total_delay += max(0, delay)
            
            if delay <= 0:
                on_time += 1

        # 2. Mettre à jour le fournisseur
        supplier_result = await self.db.execute(
            select(Supplier).where(Supplier.id == supplier_id)
        )
        supplier = supplier_result.scalar_one()
        
        supplier.reliability_score = on_time / total
        supplier.average_delay_days = total_delay / total
        
        await self.db.flush()
        return supplier

    async def create_purchase_order(self, shop_id: str, product_id: str, supplier_id: str, quantity: int, lead_time: int):
        """Crée un nouveau PO avec date de réception prévue."""
        expected_date = date.today() # + lead_time (Logique simplifiée pour MVP)
        # TODO: implémenter le calcul de la date d'arrivée réaliste
        pass
