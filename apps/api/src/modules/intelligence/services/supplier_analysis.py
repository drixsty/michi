"""
Supplier Analysis Service — Data Science Intelligence Module

Calcule les métriques de performance fournisseur (fiabilité, délai moyen, sigma LT)
à partir des Purchase Orders historiques complétés.

Corrections Sprint 26 :
    - ddof=1 (std échantillon) au lieu de ddof=0 (std population) pour lt_sigma.
      Sur 5 POs, ddof=0 sous-estime la variance de ~10%, ce qui réduit le safety stock
      calculé par la formule Z×√(LT×σd²+D²×σlt²) — ruptures réelles en production.
"""
import numpy as np
from uuid import UUID
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.inventory.infrastructure.persistence.models import Supplier, PurchaseOrder


class SupplierAnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_supplier_metrics(self, supplier_id: UUID) -> Dict[str, float]:
        """
        Analyse tous les POs COMPLETED pour un fournisseur et met à jour ses métriques.

        Returns:
            {"reliability": float, "average_delay": float, "lead_time_sigma": float}
        """
        stmt = (
            select(PurchaseOrder)
            .where(PurchaseOrder.supplier_id == supplier_id)
            .where(PurchaseOrder.status == "COMPLETED")
            .where(PurchaseOrder.actual_arrival_date != None)  # noqa: E711
        )
        result = await self.session.execute(stmt)
        pos = result.scalars().all()

        if not pos:
            return {"reliability": 1.0, "average_delay": 0.0, "lead_time_sigma": 0.0}

        delays = []
        lead_times = []
        on_time_count = 0

        for po in pos:
            delay = (po.actual_arrival_date - po.expected_arrival_date).days
            delays.append(delay)
            lead_times.append((po.actual_arrival_date - po.order_date).days)
            if delay <= 0:
                on_time_count += 1

        avg_delay = np.mean(delays)
        reliability = on_time_count / len(pos)
        # ddof=1 : std échantillon — évite la sous-estimation sur petits lots de POs
        lt_sigma = np.std(lead_times, ddof=1) if len(lead_times) > 1 else 0.0

        stmt_supplier = select(Supplier).where(Supplier.id == supplier_id)
        supplier_model = (await self.session.execute(stmt_supplier)).scalar_one_or_none()

        if supplier_model:
            supplier_model.reliability_score = reliability  # type: ignore[assignment]
            supplier_model.average_delay_days = avg_delay   # type: ignore[assignment]
            supplier_model.lead_time_sigma = lt_sigma       # type: ignore[assignment]

        await self.session.flush()

        return {
            "reliability": float(reliability),
            "average_delay": avg_delay,
            "lead_time_sigma": float(lt_sigma),
        }

    async def analyze_all_suppliers(self, store_id: UUID) -> Dict[str, Dict[str, float]]:
        """Analyse en lot tous les fournisseurs d'un store."""
        stmt = select(Supplier).where(Supplier.store_id == store_id)
        suppliers = (await self.session.execute(stmt)).scalars().all()

        results: Dict[str, Dict[str, float]] = {}
        for s in suppliers:
            sid = UUID(str(s.id))
            metrics = await self.update_supplier_metrics(sid)
            results[str(sid)] = metrics

        return results
