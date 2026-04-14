"""
Health Score Algorithm — Sprint 14 (extrait de decisions/service.py Sprint 21)

Calcule un score de santé inventaire de 0 à 100 basé sur 3 composantes :

    avail  = 1 - (revenue_at_risk / total_potential)   # disponibilité du CA
    rot    = f(avg_coverage_days)                       # rotation du stock
    out    = 1 - (stockout_count / total_skus)          # taux de rupture

    health_score = round((avail * 0.5 + rot * 0.3 + out * 0.2) * 100)

Formule de rotation (rot) :
    - coverage < 7j  : rot = coverage / 7         (stock critique)
    - 7j <= cov <= 45j: rot = 1.0                 (optimal)
    - 45j < cov <= 90j: rot = 1 - (cov-45) / 45  (sur-stockage léger)
    - coverage > 90j : rot = max(0, 0.5 - (cov-90) / 180)  (sur-stockage fort)

Performance : O(1) — fonction pure.
"""
from __future__ import annotations


def calculate_health_score(
    revenue_at_risk: float,
    total_run_rate: float,
    avg_sale_price: float,
    avg_coverage_days: float,
    stockout_count: int,
    total_skus: int,
) -> int:
    """
    Calcule le Health Score inventaire (0-100).

    Args:
        revenue_at_risk: CA à risque (valeur des commandes urgentes à passer).
        total_run_rate: Run rate total journalier de tous les SKUs.
        avg_sale_price: Prix de vente moyen par unité.
        avg_coverage_days: Couverture moyenne en jours sur tous les SKUs.
        stockout_count: Nombre de SKUs avec stock <= 0.
        total_skus: Nombre total de SKUs actifs.

    Returns:
        Score entier entre 0 et 100.

    Example:
        >>> calculate_health_score(0, 10, 50, 30, 0, 100)
        100
        >>> calculate_health_score(5000, 10, 50, 3, 5, 100)
        # Score dégradé : peu de couverture + ruptures + CA à risque
    """
    # 1. Composante disponibilité CA
    forecasted_30d = total_run_rate * 30 * avg_sale_price
    total_potential = forecasted_30d + revenue_at_risk
    avail = 1.0 - (revenue_at_risk / total_potential) if total_potential > 0 else 1.0

    # 2. Composante rotation
    if avg_coverage_days < 7:
        rot = avg_coverage_days / 7
    elif avg_coverage_days <= 45:
        rot = 1.0
    elif avg_coverage_days <= 90:
        rot = 1.0 - (avg_coverage_days - 45) / 45
    else:
        rot = max(0.0, 0.5 - (avg_coverage_days - 90) / 180)

    # 3. Composante rupture
    out_ratio = 1.0 - (stockout_count / total_skus) if total_skus > 0 else 1.0

    return max(0, min(100, round((avail * 0.5 + rot * 0.3 + out_ratio * 0.2) * 100)))
