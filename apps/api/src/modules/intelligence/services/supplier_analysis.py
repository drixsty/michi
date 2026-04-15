"""
Supplier Analysis Service — Data Science Intelligence Module
Calculates performance metrics (reliability, average delay, sigma LT) from historical Purchase Orders.
"""
import numpy as np
import math
from uuid import UUID
from datetime import date
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.inventory.infrastructure.persistence.models import Supplier, PurchaseOrder
from modules.inventory.domain.entities import SupplierEntity

class SupplierAnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_supplier_metrics(self, supplier_id: UUID) -> Dict[str, float]:
        """
        Analyses all COMPLETED purchase orders for a supplier and updates its metrics.
        Returns a dict of new metrics.
        """
        # 1. Fetch historical completed POs
        stmt = (
            select(PurchaseOrder)
            .where(PurchaseOrder.supplier_id == supplier_id)
            .where(PurchaseOrder.status == "COMPLETED")
            .where(PurchaseOrder.actual_arrival_date != None)
        )
        result = await self.session.execute(stmt)
        pos = result.scalars().all()

        if not pos:
            return {"reliability": 1.0, "average_delay": 0.0, "lead_time_sigma": 0.0}

        # 2. Extract delays and lead times
        delays = []
        lead_times = []
        
        on_time_count = 0
        total_count = len(pos)

        for po in pos:
            # Delay relative to EXPECTED (in days)
            delay = (po.actual_arrival_date - po.expected_arrival_date).days
            delays.append(delay)
            
            # Real Lead Time (order to actual)
            real_lt = (po.actual_arrival_date - po.order_date).days
            lead_times.append(real_lt)

            if delay <= 0:
                on_time_count += 1

        # 3. Calculate statistics
        avg_delay = float(np.mean(delays))
        reliability = float(on_time_count / total_count)
        
        # Sigma LT (volatility of delivery time)
        lt_sigma = float(np.std(lead_times)) if len(lead_times) > 1 else 0.0

        # 4. Update Supplier record
        stmt_supplier = select(Supplier).where(Supplier.id == supplier_id)
        supplier_model = (await self.session.execute(stmt_supplier)).scalar_one_or_none()
        
        if supplier_model:
            supplier_model.reliability_score = reliability
            supplier_model.average_delay_days = avg_delay
            supplier_model.lead_time_sigma = lt_sigma
        
        await self.session.flush()
        
        return {
            "reliability": reliability,
            "average_delay": avg_delay,
            "lead_time_sigma": lt_sigma
        }

    async def analyze_all_suppliers(self, store_id: UUID):
        """Batch analysis for all suppliers in a store."""
        stmt = select(Supplier).where(Supplier.store_id == store_id)
        suppliers = (await self.session.execute(stmt)).scalars().all()
        
        results = {}
        for s in suppliers:
            metrics = await self.update_supplier_metrics(s.id)
            results[s.id] = metrics
            
        return results
