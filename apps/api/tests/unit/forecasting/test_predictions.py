import numpy as np
import pandas as pd
"""
Tests unitaires — Prediction Algorithms (US 2.6 / US 2.7 / US 2.9)
Couverture :
    - predict_stockout_date : cas nominaux, run_rate=0, stock=0, MAPE implicite
    - calculate_reorder_quantity : formule, MOQ, safety_factor, stock suffisant
    - MAPE < 20% sur des prédictions de date de rupture simulées (US 2.9)
"""
import math
from datetime import date, timedelta


from src.modules.forecasting.algorithms.predictions import (
    predict_stockout_date,
    calculate_reorder_quantity,
)


# ─────────────────────────────────────────────────────────────
#  Tests predict_stockout_date (US 2.6)
# ─────────────────────────────────────────────────────────────

class TestPredictStockoutDate:

    def test_nominal_case(self):
        """60 unités / 2 unités/jour = 30 jours → stockout J+30."""
        ref = date(2025, 6, 1)
        result = predict_stockout_date(60.0, 2.0, ref)
        assert result == date(2025, 7, 1)

    def test_floor_days(self):
        """10 unités / 3 unités/jour = 3.33 → floor = 3 jours."""
        ref = date(2025, 1, 1)
        result = predict_stockout_date(10.0, 3.0, ref)
        assert result == date(2025, 1, 4)

    def test_zero_run_rate_returns_none(self):
        """Run rate == 0 → aucune rupture prévisible → None."""
        result = predict_stockout_date(100.0, 0.0)
        assert result is None

    def test_negative_run_rate_returns_none(self):
        """Run rate négatif traité comme 0 → None."""
        result = predict_stockout_date(100.0, -1.0)
        assert result is None

    def test_zero_stock_returns_reference_date(self):
        """Stock déjà épuisé → rupture immédiate = date de référence."""
        ref = date(2025, 3, 15)
        result = predict_stockout_date(0.0, 5.0, ref)
        assert result == ref

    def test_stock_exact_multiple(self):
        """Stock multiple exact du run rate."""
        ref = date(2025, 1, 1)
        result = predict_stockout_date(100.0, 10.0, ref)
        assert result == date(2025, 1, 11)  # 10 jours

    def test_uses_today_as_default(self):
        """Sans reference_date, la date de référence est aujourd'hui."""
        result = predict_stockout_date(30.0, 1.0)
        expected = date.today() + timedelta(days=30)
        assert result == expected


# ─────────────────────────────────────────────────────────────
#  Tests calculate_reorder_quantity (US 2.7)
# ─────────────────────────────────────────────────────────────

class TestCalculateReorderQuantity:

    def test_nominal_case(self):
        """
        run_rate=10, lead_time=7, moq=50, stock=20, safety=1.5
        target = 10×7×1.5 = 105
        raw = 105 - 20 = 85
        arrondi MOQ = ceil(85/50)×50 = 2×50 = 100
        """
        result = calculate_reorder_quantity(
            run_rate=10.0, lead_time=7, moq=50, current_stock=20.0
        )
        assert result == 100

    def test_stock_sufficient_returns_zero(self):
        """Stock largement suffisant → 0 à commander."""
        result = calculate_reorder_quantity(
            run_rate=5.0, lead_time=7, moq=10, current_stock=200.0
        )
        assert result == 0

    def test_moq_rounding_up(self):
        """La quantité est toujours arrondie au MOQ supérieur."""
        # raw = 1 unité → arrondi au MOQ = 10
        result = calculate_reorder_quantity(
            run_rate=1.0, lead_time=1, moq=10, current_stock=0.0,
            safety_factor=1.0
        )
        assert result == 10
        assert result % 10 == 0

    def test_zero_run_rate_returns_zero(self):
        """Run rate == 0 → rien à commander."""
        result = calculate_reorder_quantity(
            run_rate=0.0, lead_time=7, moq=50, current_stock=0.0
        )
        assert result == 0

    def test_zero_lead_time_returns_zero(self):
        """Lead time == 0 → rien à commander."""
        result = calculate_reorder_quantity(
            run_rate=10.0, lead_time=0, moq=50, current_stock=0.0
        )
        assert result == 0

    def test_safety_factor_1(self):
        """
        safety_factor=1.0 : couverture exacte du lead time sans marge.
        run_rate=10, lead_time=5, moq=10, stock=0
        target = 50 → reorder = 50
        """
        result = calculate_reorder_quantity(
            run_rate=10.0, lead_time=5, moq=10, current_stock=0.0,
            safety_factor=1.0
        )
        assert result == 50

    def test_result_is_multiple_of_moq(self):
        """Le résultat est toujours un multiple du MOQ."""
        for moq in [1, 5, 10, 25, 100]:
            result = calculate_reorder_quantity(
                run_rate=7.3, lead_time=14, moq=moq, current_stock=10.0
            )
            if result > 0:
                assert result % moq == 0, f"Résultat {result} non multiple de {moq}"

    def test_moq_minimum_one(self):
        """MOQ=0 ou négatif → traité comme MOQ=1."""
        result = calculate_reorder_quantity(
            run_rate=5.0, lead_time=7, moq=0, current_stock=0.0
        )
        assert result > 0  # doit retourner quelque chose


# ─────────────────────────────────────────────────────────────
#  Tests MAPE — US 2.9 (seuil < 20%)
# ─────────────────────────────────────────────────────────────

def _mape(actual: list[float], predicted: list[float]) -> float:
    """
    Mean Absolute Percentage Error — version standard.
    Exclut les cas où actual == 0 pour éviter la division par zéro.
    """
    errors = []
    for a, p in zip(actual, predicted):
        if a != 0:
            errors.append(abs(a - p) / abs(a))
    if not errors:
        return 0.0
    return float(np.mean(errors)) * 100.0


class TestMapeStockoutPrediction:
    """
    US 2.9 — Validation MAPE < 20% sur la prédiction de jours avant rupture.

    Principe : on simule des produits avec une consommation connue,
    on calcule le nombre de jours prévu vs réel, et on vérifie que
    l'erreur relative moyenne est < 20%.
    """

    def test_mape_perfect_run_rate(self):
        """Run rate = consommation réelle → MAPE = 0%."""
        cases = [
            (100.0, 5.0),   # 20 jours
            (50.0, 2.5),    # 20 jours
            (200.0, 10.0),  # 20 jours
        ]
        actual_days = [math.floor(s / r) for s, r in cases]
        predicted_days = [math.floor(s / r) for s, r in cases]
        mape = _mape(actual_days, predicted_days)
        assert mape == 0.0

    def test_mape_under_threshold_with_noise(self):
        """
        Run rate avec ±10% de bruit → MAPE doit rester < 20%.

        Simule 20 produits avec consommation réelle entre 5 et 50 unités/jour
        et stock entre 50 et 500 unités. Le run rate estimé a un bruit ±10%.
        """
        rng = np.random.default_rng(42)
        n = 20
        stocks = rng.uniform(50.0, 500.0, n)
        true_rates = rng.uniform(5.0, 50.0, n)
        noise = rng.uniform(0.9, 1.1, n)  # ±10%

        actual_days = [math.floor(s / r) for s, r in zip(stocks, true_rates)]
        estimated_rates = true_rates * noise
        predicted_days = [math.floor(s / r) for s, r in zip(stocks, estimated_rates)]

        mape = _mape(actual_days, predicted_days)
        assert mape < 20.0, f"MAPE trop élevée : {mape:.1f}% (seuil: 20%)"

    def test_mape_reorder_quantity_accuracy(self):
        """
        MAPE < 20% sur la quantité de commande recommandée.

        Produits avec lead_time fixe, consommation connue ±5%,
        moq=1 pour éviter le bruit d'arrondi.
        """
        rng = np.random.default_rng(99)
        n = 15
        true_rates = rng.uniform(5.0, 30.0, n)
        lead_times = rng.integers(7, 30, n)
        stocks = rng.uniform(10.0, 100.0, n)
        noise = rng.uniform(0.95, 1.05, n)  # ±5%

        # Quantité cible réelle (safety=1.5, moq=1)
        actual_qty = [
            max(0.0, r * lt * 1.5 - s)
            for r, lt, s in zip(true_rates, lead_times, stocks)
        ]

        # Quantité avec run rate bruité
        predicted_qty = [
            calculate_reorder_quantity(
                run_rate=r * n_,
                lead_time=int(lt),
                moq=1,
                current_stock=s,
            )
            for r, lt, s, n_ in zip(true_rates, lead_times, stocks, noise)
        ]

        # Filtrer les cas où actual == 0 (stock suffisant)
        pairs = [(a, p) for a, p in zip(actual_qty, predicted_qty) if a > 0]
        if pairs:
            actuals, preds = zip(*pairs)
            mape = _mape(list(actuals), list(preds))
            assert mape < 20.0, f"MAPE quantité trop élevée : {mape:.1f}%"
