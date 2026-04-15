"""
Risk Scoring — Sprint 21 (extrait de decisions/service.py)

Calcule les scores de risque par SKU à partir de l'agrégation SKU et produit
le top_risks trié par valeur de risque décroissante.

Entrée  : sku_aggregation dict produit par le premier pass de decisions/service.py
          (après agrégation stocks + prédictions, avant calcul de métriques unifiées)
Sortie  : list[RiskItem] triée par risk_value DESC

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
    days_of_stock: float
    run_rate: float
    supplier_id: Optional[str]
    source_platform: str
    cost_price: float
    sale_price: float
    coverage_days: float


def score_products(
    sku_aggregation: dict[str, dict[str, Any]],
) -> tuple[list[RiskItem], float]:
    """
    Calcule les scores de risque SKU et retourne les items triés.

    Effectue le second pass sur l'agrégation SKU :
    - Calcule coverage_days = stock / run_rate (ou 999 si run_rate == 0)
    - Calcule stockout_date = today + coverage_days
    - Construit la liste RiskItem triée par risk_value DESC

    Args:
        sku_aggregation: Dict {sku: {stock, run_rate, risk_value, reorder_quantity,
                                     product_id, title, supplier_id, platforms,
                                     cost, sale, ...}}
                         tel que produit par le premier pass de decisions/service.py.

    Returns:
        Tuple (risk_items, avg_coverage_days) où :
        - risk_items: liste triée par risk_value DESC
        - avg_coverage_days: couverture moyenne en jours (sur SKUs avec run_rate > 0)

    Example:
        >>> agg = {
        ...     "SKU001": {
        ...         "product_id": "abc", "stock": 50, "run_rate": 5.0,
        ...         "risk_value": 200.0, "reorder_quantity": 10,
        ...         "title": "Produit A", "supplier_id": None,
        ...         "platforms": {"SHOPIFY"}, "cost": 10.0, "sale": 20.0,
        ...     }
        ... }
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

        # Calcul couverture
        if run_rate > 0:
            coverage_days = stock / run_rate
            stockout_date = today + timedelta(days=max(0, int(coverage_days)))
            total_coverage_days += coverage_days
            products_with_runrate += 1
        else:
            coverage_days = 999.0
            stockout_date = None

        # Mettre à jour l'agrégation pour usage downstream si nécessaire
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
                days_of_stock=round(coverage_days, 1),
                run_rate=round(run_rate, 4),
                supplier_id=agg.get("supplier_id"),
                source_platform=source_platform,
                cost_price=round(agg.get("cost", 0.0), 2),
                sale_price=round(agg.get("sale", 0.0), 2),
                coverage_days=coverage_days,
            )
        )

    # Tri par risk_value décroissant
    risk_items.sort(key=lambda x: x.risk_value, reverse=True)

    avg_coverage_days = (
        total_coverage_days / products_with_runrate
        if products_with_runrate > 0
        else 0.0
    )

    return risk_items, avg_coverage_days
