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
    sigma: float = 0.0,
    service_level: float = 0.95,
    average_delay: float = 0.0,
    lead_time_sigma: float = 0.0,
) -> int:
    """
    Calcule la quantité de commande recommandée via modèle statistique (Sprint 22).

    Formule (Service Level driven) avec variabilité combinée :
        SafetyStock = Z * sqrt( LT * σ_demand² + RunRate² * σ_lt² )
        Target      = (RunRate * LT_effective) + SafetyStock
        Reorder     = ceil(max(0, Target - CurrentStock) / MOQ) * MOQ

    Args:
        run_rate: Taux de vente quotidien moyen (>= 0).
        lead_time: Délai de livraison théorique en jours (>= 1).
        moq: Quantité minimum de commande (>= 1).
        current_stock: Stock actuel.
        sigma: Écart-type de la demande (volatilité).
        service_level: Probabilité de ne pas être en rupture (défaut: 0.95).
        average_delay: Retard moyen constaté du fournisseur.
        lead_time_sigma: Écart-type du délai de livraison (incertitude fournisseur).

    Returns:
        Quantité à commander (multiple de moq).
    """
    if run_rate <= 0.0 or lead_time <= 0:
        return 0

    moq = max(1, moq)
    effective_lead_time = lead_time + average_delay
    
    # 1. Calcul du coefficient Z
    z_map = {0.90: 1.282, 0.95: 1.645, 0.99: 2.326}
    z_score = z_map.get(service_level, 1.645)

    # 2. Calcul du besoin de fond (Cycle Stock)
    cycle_stock = run_rate * effective_lead_time
    
    # 3. Calcul du Stock de Sécurité Statistique (Variabilité combinée)
    # Formule : Z * sqrt( (LT * σ_d²) + (D² * σ_lt²) )
    combined_variance = (effective_lead_time * (sigma ** 2)) + ((run_rate ** 2) * (lead_time_sigma ** 2))
    safety_stock = z_score * math.sqrt(combined_variance)
    
    # 4. Cible de stock et calcul de commande
    target_stock = cycle_stock + safety_stock
    raw_qty = max(0.0, target_stock - current_stock)

    if raw_qty == 0.0:
        return 0

    return math.ceil(raw_qty / moq) * moq
