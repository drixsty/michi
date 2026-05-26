"""
Risk Scoring — Sprint 21 (corrigé Sprint 26)

Calcule les scores de risque par SKU et produit le top_risks trié par valeur de risque DESC.

Corrections Sprint 26 :
    - int(coverage_days) → round(coverage_days) : la troncature (= floor) sous-estimait
      systématiquement la date de stockout d'un jour (ex : 28.9j → 28j au lieu de 29j).
    - coverage_days = None (au lieu de 999.0) quand run_rate == 0 : le magic number 999
      pouvait propager des calculs incohérents si utilisé dans des agrégations downstream.

Performance : O(n log n) — tri final seulement.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Optional


@dataclass(frozen=True)
class RiskItem:
    """Résultat du scoring de risque pour un SKU."""
    product_id: str
    sku: str
    title: str
    risk_value: float
    stockout_date: Optional[date]
    reorder_quantity: int
    days_of_stock: Optional[float]
    run_rate: float
    supplier_id: Optional[str]
    source_platform: str
    cost_price: float
    sale_price: float
    coverage_days: Optional[float]


def score_products(
    sku_aggregation: dict[str, dict[str, Any]],
) -> tuple[list[RiskItem], float]:
    """
    Calcule les scores de risque SKU et retourne les items triés.

    Args:
        sku_aggregation: Dict {sku: {stock, run_rate, risk_value, reorder_quantity,
                                     product_id, title, supplier_id, platforms,
                                     cost, sale, ...}}

    Returns:
        Tuple (risk_items, avg_coverage_days) :
        - risk_items : liste triée par risk_value DESC
        - avg_coverage_days : moyenne en jours (SKUs avec run_rate > 0 uniquement)

    Example:
        >>> agg = {"SKU001": {"product_id": "abc", "stock": 50, "run_rate": 5.0,
        ...                   "risk_value": 200.0, "reorder_quantity": 10,
        ...                   "title": "Produit A", "supplier_id": None,
        ...                   "platforms": {"SHOPIFY"}, "cost": 10.0, "sale": 20.0}}
        >>> items, avg_cov = score_products(agg)
        >>> items[0].days_of_stock
        10.0
        >>> avg_cov
        10.0
    """
    today = date.today()
    risk_items: list[RiskItem] = []
    total_coverage_days = 0.0
    products_with_runrate = 0

    for sku, agg in sku_aggregation.items():
        stock = agg.get("stock", 0)
        run_rate = agg.get("run_rate", 0.0)

        if run_rate > 0:
            coverage_days = stock / run_rate
            # round() au lieu de int()/floor() : évite la sous-estimation systématique d'un jour
            stockout_date = today + timedelta(days=max(0, round(coverage_days)))
            total_coverage_days += coverage_days
            products_with_runrate += 1
        else:
            coverage_days = None
            stockout_date = None

        agg["coverage_days"] = coverage_days
        agg["stockout_date"] = stockout_date

        platforms = agg.get("platforms", set())
        source_platform = (
            ",".join(sorted(platforms))
            if isinstance(platforms, (set, list))
            else str(platforms)
        )

        risk_items.append(
            RiskItem(
                product_id=str(agg.get("product_id", "")),
                sku=sku,
                title=agg.get("title", "Sans titre"),
                risk_value=round(agg.get("risk_value", 0.0), 2),
                stockout_date=stockout_date,
                reorder_quantity=agg.get("reorder_quantity", 0),
                days_of_stock=round(coverage_days, 1) if coverage_days is not None else None,
                run_rate=round(run_rate, 4),
                supplier_id=agg.get("supplier_id"),
                source_platform=source_platform,
                cost_price=round(agg.get("cost", 0.0), 2),
                sale_price=round(agg.get("sale", 0.0), 2),
                coverage_days=coverage_days,
            )
        )

    risk_items.sort(key=lambda x: x.risk_value, reverse=True)

    avg_coverage_days = (
        total_coverage_days / products_with_runrate
        if products_with_runrate > 0
        else 0.0
    )

    return risk_items, avg_coverage_days
