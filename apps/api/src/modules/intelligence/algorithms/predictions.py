"""
Prediction Algorithms — US 2.6 / US 2.7 (Sprint 4, corrigé Sprint 26-27)

Fonctions :
    predict_stockout_date       — date prévisionnelle de rupture
    calculate_reorder_quantity  — quantité de commande (safety stock statistique)
    calculate_reorder_alert_date — date limite de déclenchement de la commande (ROP date)

Corrections Sprint 26 :
    - math.floor → round : la troncature systématique sous-estimait la date de rupture.
    - Z-score via scipy.stats.norm.ppf : table discrète remplacée par calcul continu.
    - Ajout de calculate_reorder_alert_date (ROP date).

Correction Sprint 27 — stock en transit (POs) :
    Problème : predict_stockout_date(stock=50, run_rate=10) → rupture dans 5 jours.
    Si un PO de 100 unités arrive dans 3 jours, l'alerte est une fausse alarme.
    L'acheteur reçoit une alerte urgente alors que le stock va être réapprovisionné.

    Fix : paramètre stock_in_transit (somme des quantités des POs dont le statut est
    actif — PENDING/CONFIRMED/SHIPPED — et dont l'expected_arrival_date est >= today).
    effective_stock = current_stock + stock_in_transit

    Note : pour simplifier, tous les POs en transit sont ajoutés (sans simulation
    jour-par-jour). C'est conservateur : si 2 POs arrivent à des dates différentes,
    on additionne leurs quantités. Acceptable car le scénario d'erreur inverse (fausse
    alerte) est plus coûteux que le scénario optimiste.

Formule safety stock (Silver-Pyke-Peterson §7.4) :
    SS = Z × √( LT_eff × σd² + D² × σlt² )
    Target = D × LT_eff + SS
    Reorder = ceil( max(0, Target - Stock) / MOQ ) × MOQ

Performance : O(1) par produit — fonctions pures sans I/O.
"""
import math
from datetime import date, timedelta
from scipy.stats import norm


def predict_stockout_date(
    current_stock: float,
    run_rate: float,
    reference_date: date | None = None,
    stock_in_transit: float = 0.0,
) -> date | None:
    """
    Prédit la date de rupture de stock à partir du run rate.

    Args:
        current_stock: Stock actuel en unités (>= 0).
        run_rate: Taux de vente quotidien en unités/jour (>= 0).
        reference_date: Date de référence (défaut : aujourd'hui).
        stock_in_transit: Quantité totale des POs actifs attendus (>= 0).
                          Additionné au stock actuel pour éviter les fausses alertes
                          quand une commande fournisseur est déjà en route.

    Returns:
        Date prévisionnelle de rupture, ou None si run_rate == 0.

    Example:
        >>> from datetime import date
        >>> predict_stockout_date(60.0, 2.0, date(2025, 6, 1))
        datetime.date(2025, 7, 1)
        >>> predict_stockout_date(10.0, 2.0, date(2025, 6, 1), stock_in_transit=50.0)
        datetime.date(2025, 7, 1)  # same result: 60 effective units / 2 = 30 days
        >>> predict_stockout_date(100.0, 0.0) is None
        True
    """
    if run_rate <= 0.0:
        return None

    effective_stock = current_stock + max(0.0, stock_in_transit)
    if effective_stock <= 0.0:
        return reference_date or date.today()

    ref = reference_date or date.today()
    days_until_stockout = round(effective_stock / run_rate)
    return ref + timedelta(days=days_until_stockout)


def calculate_reorder_alert_date(
    stockout_date: date,
    lead_time: int,
    average_delay: float = 0.0,
) -> date:
    """
    Calcule la date limite à laquelle la commande doit être passée (Reorder Point date).

    Sans cette date, un utilisateur qui voit "rupture dans 14j" avec un fournisseur
    à LT=21j est structurellement en retard — la valeur produit est annulée.

    Formule :
        reorder_alert_date = stockout_date - effective_lead_time
        effective_lead_time = ceil(lead_time + max(0, average_delay))

    Args:
        stockout_date: Date prévisionnelle de rupture (depuis predict_stockout_date).
        lead_time: Délai de livraison théorique en jours (>= 1).
        average_delay: Retard moyen constaté du fournisseur (en jours, peut être négatif
                       si le fournisseur livre souvent en avance).

    Returns:
        Date à laquelle passer la commande pour recevoir le stock avant la rupture.
        Peut être dans le passé (commande en retard → alerte urgente).

    Example:
        >>> from datetime import date
        >>> calculate_reorder_alert_date(date(2025, 7, 15), lead_time=21)
        datetime.date(2025, 6, 24)
    """
    effective_lt = math.ceil(lead_time + max(0.0, average_delay))
    return stockout_date - timedelta(days=effective_lt)


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

    Formule (Silver-Pyke-Peterson §7.4) :
        SS     = Z × √( LT_eff × σd² + D² × σlt² )
        Target = D × LT_eff + SS
        Reorder = ceil( max(0, Target - Stock) / MOQ ) × MOQ

    Args:
        run_rate: Taux de vente quotidien moyen (>= 0).
        lead_time: Délai de livraison théorique en jours (>= 1).
        moq: Quantité minimum de commande (>= 1).
        current_stock: Stock actuel.
        sigma: Écart-type de la demande journalière (volatilité).
        service_level: Probabilité de ne pas être en rupture pendant le LT (défaut: 0.95).
        average_delay: Retard moyen constaté du fournisseur en jours.
        lead_time_sigma: Écart-type du délai de livraison (incertitude fournisseur).

    Returns:
        Quantité à commander (multiple de moq). 0 si stock suffisant.
    """
    if run_rate <= 0.0 or lead_time <= 0:
        return 0

    moq = max(1, moq)
    effective_lead_time = lead_time + average_delay

    # Z-score continu via scipy — couvre tous les niveaux de service, pas seulement 0.90/0.95/0.99
    z_score = norm.ppf(max(0.5, min(0.9999, service_level)))

    cycle_stock = run_rate * effective_lead_time
    combined_variance = (effective_lead_time * (sigma ** 2)) + ((run_rate ** 2) * (lead_time_sigma ** 2))
    safety_stock = z_score * math.sqrt(combined_variance)

    target_stock = cycle_stock + safety_stock
    raw_qty = max(0.0, target_stock - current_stock)

    if raw_qty == 0.0:
        return 0

    return math.ceil(raw_qty / moq) * moq
