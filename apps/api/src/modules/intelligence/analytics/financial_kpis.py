"""
Financial KPIs — Sprint 13 (extrait de decisions/service.py Sprint 21)

Calcule les indicateurs financiers d'inventaire à partir de données produits+prédictions.

Métriques :
    inventory_value_cost  = sum(stock × cost_price)
    inventory_value_sale  = sum(stock × sale_price)
    revenue_at_risk       = sum(reorder_quantity × sale_price)  — voir définition ci-dessous
    stock_coverage_avg    = mean(stock / run_rate)  pour les produits avec run_rate > 0

DÉFINITION EXACTE de revenue_at_risk :
    C'est la VALEUR DES COMMANDES À PASSER pour éviter les ruptures à venir,
    pas le chiffre d'affaires déjà perdu sur des ruptures actuelles.
    Formule : Σ (reorder_quantity × sale_price) pour les SKUs nécessitant un réappro.

    Interprétation métier : "Si vous ne passez pas ces commandes maintenant,
    vous risquez de manquer X€ de ventes dans les prochaines semaines."

    ⚠️  NE PAS confondre avec :
    - Le CA perdu aujourd'hui sur des ruptures actuelles (c'est une perte déjà réalisée).
    - Le chiffre d'affaires total à risque si aucune commande n'est jamais passée.

Performance : O(n) vectorisé.
"""
from dataclasses import dataclass
from typing import Any  # noqa: F401 — used in dict[str, Any] annotation below


@dataclass(frozen=True)
class FinancialKpis:
    """Résultat du calcul des KPIs financiers."""
    inventory_value_cost: float
    inventory_value_sale: float
    revenue_at_risk: float
    stock_coverage_avg_days: float
    total_run_rate: float
    total_stock: int
    avg_sale_price: float


def calculate_financial_kpis(
    sku_aggregation: dict[str, dict[str, Any]],
) -> FinancialKpis:
    """
    Calcule les KPIs financiers à partir de l'agrégation SKU.

    Args:
        sku_aggregation: Dict {sku: {stock, cost, sale, run_rate,
                                     risk_value, coverage_days, ...}}
                         tel que produit par decisions/service.py.

    Returns:
        FinancialKpis avec toutes les métriques agrégées.

    Example:
        >>> agg = {"SKU001": {"stock": 100, "cost": 10.0, "sale": 20.0,
        ...                   "run_rate": 5.0, "risk_value": 200.0,
        ...                   "coverage_days": 20.0}}
        >>> kpis = calculate_financial_kpis(agg)
        >>> kpis.inventory_value_cost
        1000.0
    """
    inventory_value_cost = 0.0
    inventory_value_sale = 0.0
    revenue_at_risk = 0.0
    total_coverage_days = 0.0
    products_with_runrate = 0
    total_run_rate = 0.0
    total_stock = 0

    for agg in sku_aggregation.values():
        stock = agg.get("stock", 0)
        cost = agg.get("cost", 0.0)
        sale = agg.get("sale", 0.0)
        run_rate = agg.get("run_rate", 0.0)
        risk_value = agg.get("risk_value", 0.0)
        coverage_days = agg.get("coverage_days")

        inventory_value_cost += stock * cost
        inventory_value_sale += stock * sale
        revenue_at_risk += risk_value
        total_run_rate += run_rate
        total_stock += stock

        if coverage_days is not None and run_rate > 0:
            total_coverage_days += coverage_days
            products_with_runrate += 1

    avg_coverage = (
        total_coverage_days / products_with_runrate
        if products_with_runrate > 0
        else 0.0
    )
    avg_sale_price = inventory_value_sale / total_stock if total_stock > 0 else 0.0

    return FinancialKpis(
        inventory_value_cost=round(inventory_value_cost, 2),
        inventory_value_sale=round(inventory_value_sale, 2),
        revenue_at_risk=round(revenue_at_risk, 2),
        stock_coverage_avg_days=round(avg_coverage, 1),
        total_run_rate=total_run_rate,
        total_stock=total_stock,
        avg_sale_price=avg_sale_price,
    )
