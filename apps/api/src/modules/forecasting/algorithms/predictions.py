"""
Prediction Algorithms — US 2.6 / US 2.7 (Sprint 4)

Objectif :
    Deux fonctions de prédiction opérationnelle à partir du run rate :

    US 2.6 — Date de rupture prévisionnelle :
        stockout_date = today + floor(current_stock / run_rate)
        Si run_rate == 0 → None (stock infini, pas de rupture prévisible)

    US 2.7 — Quantité de commande recommandée :
        reorder_qty = max(0, run_rate × lead_time × safety_factor - current_stock)
        Arrondi au MOQ supérieur (Multiple Of Quantity).

        safety_factor (défaut 1.5) : marge de sécurité pour absorber la variabilité
        de la demande et les délais de livraison incertains.

Formules détaillées :

    stockout_in_days = floor(current_stock / run_rate)   # nb jours de stock restant
    stockout_date    = today + timedelta(days=stockout_in_days)

    demand_over_lead_time = run_rate × lead_time
    safety_buffer         = demand_over_lead_time × (safety_factor - 1)
    target_stock          = demand_over_lead_time + safety_buffer  = run_rate × lead_time × safety_factor
    reorder_qty_raw       = max(0, target_stock - current_stock)
    reorder_qty           = ceil(reorder_qty_raw / moq) × moq   # arrondi MOQ supérieur

Hypothèses :
    - run_rate en unités/jour
    - lead_time en jours
    - moq ≥ 1 (minimum order quantity)
    - current_stock ≥ 0

Performance :
    O(1) par produit — fonctions pures sans I/O.
"""
import math
from datetime import date, timedelta


def predict_stockout_date(
    current_stock: float,
    run_rate: float,
    reference_date: date | None = None,
) -> date | None:
    """
    Prédit la date de rupture de stock à partir du run rate.

    Args:
        current_stock: Stock actuel en unités (>= 0).
        run_rate: Taux de vente quotidien en unités/jour (>= 0).
        reference_date: Date de référence pour le calcul (défaut: aujourd'hui).

    Returns:
        Date prévisionnelle de rupture, ou None si run_rate == 0
        (stock dure indéfiniment) ou current_stock <= 0 (déjà en rupture).

    Example:
        >>> from datetime import date
        >>> predict_stockout_date(60.0, 2.0, date(2025, 6, 1))
        datetime.date(2025, 7, 1)
        >>> predict_stockout_date(100.0, 0.0) is None
        True
    """
    if run_rate <= 0.0:
        return None  # pas de consommation → pas de rupture prévisible
    if current_stock <= 0.0:
        # Déjà en rupture : retourner la date de référence (rupture immédiate)
        ref = reference_date or date.today()
        return ref

    ref = reference_date or date.today()
    days_until_stockout = math.floor(current_stock / run_rate)
    return ref + timedelta(days=days_until_stockout)


def calculate_reorder_quantity(
    run_rate: float,
    lead_time: int,
    moq: int,
    current_stock: float,
    safety_factor: float = 1.5,
    average_delay: float = 0.0,
) -> int:
    """
    Calcule la quantité de commande recommandée.

    Formule :
        target  = run_rate × lead_time × safety_factor
        raw_qty = max(0, target - current_stock)
        reorder = ceil(raw_qty / moq) × moq

    Args:
        run_rate: Taux de vente quotidien en unités/jour (>= 0).
        lead_time: Délai de livraison en jours (>= 1).
        moq: Minimum Order Quantity — arrondi supérieur (>= 1).
        current_stock: Stock actuel en unités (>= 0).
        safety_factor: Multiplicateur de sécurité (défaut: 1.5).
            1.0 = couverture exacte du lead time (aucune marge)
            1.5 = 50% de marge de sécurité (recommandé)

    Returns:
        Quantité à commander en unités, multiple de ``moq``. 0 si stock suffisant.

    Example:
        >>> calculate_reorder_quantity(run_rate=10.0, lead_time=7, moq=50, current_stock=20.0)
        100
        >>> calculate_reorder_quantity(run_rate=5.0, lead_time=7, moq=10, current_stock=200.0)
        0
    """
    if run_rate <= 0.0 or lead_time <= 0:
        return 0

    moq = max(1, moq)
    # Lead time effectif = délai théorique + retard moyen constaté (Sprint 8)
    effective_lead_time = lead_time + average_delay
    target_stock = run_rate * effective_lead_time * safety_factor
    raw_qty = max(0.0, target_stock - current_stock)

    if raw_qty == 0.0:
        return 0

    # Arrondir au MOQ supérieur
    return math.ceil(raw_qty / moq) * moq
