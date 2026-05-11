"""
Tests unitaires — Out-of-Stock Correction
Migré depuis forecasting/tests/ vers intelligence/tests/ (US 21.30).
Couverture : correction OOS, fenêtre 14j, fallback médiane, edge cases.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

from modules.intelligence.algorithms.out_of_stock_correction import (
    correct_out_of_stock,
    correct_out_of_stock_batch,
    ROLLING_WINDOW,
)


def make_df(units_sold: list, stocks: list, start: date = date(2025, 1, 1)) -> pd.DataFrame:
    n = len(units_sold)
    return pd.DataFrame({
        "date": [start + timedelta(days=i) for i in range(n)],
        "units_sold": [float(u) for u in units_sold],
        "end_of_day_stock": stocks,
    })


class TestCorrectOutOfStock:

    def test_no_stockout_unchanged(self):
        """Sans rupture, theoretical_units_sold == units_sold."""
        df = make_df([5, 6, 4, 7, 5], [100] * 5)
        result = correct_out_of_stock(df)
        pd.testing.assert_series_equal(
            result["theoretical_units_sold"].round(2),
            result["units_sold"].round(2),
            check_names=False,
        )

    def test_stockout_days_flagged(self):
        """Les jours avec stock=0 sont bien flagués is_stockout=True."""
        df = make_df([5, 5, 0, 0, 5], [10, 10, 0, 0, 10])
        result = correct_out_of_stock(df)
        assert result["is_stockout"].tolist() == [False, False, True, True, False]

    def test_stockout_replaced_by_rolling_median(self):
        """Un jour de rupture est corrigé par la médiane des 14j précédents."""
        units = [10.0] * 20 + [0.0] * 5
        stocks = [100] * 20 + [0] * 5
        df = make_df(units, stocks)
        result = correct_out_of_stock(df)
        corrected = result.loc[result["is_stockout"], "theoretical_units_sold"]
        assert all(abs(v - 10.0) < 1.0 for v in corrected)

    def test_stockout_robust_to_outlier_in_window(self):
        """La médiane est robuste aux outliers dans la fenêtre (vs moyenne)."""
        units = [5.0] * 13 + [500.0] + [0.0] * 5
        stocks = [100] * 14 + [0] * 5
        df = make_df(units, stocks)
        result = correct_out_of_stock(df)
        corrected = result.loc[result["is_stockout"], "theoretical_units_sold"]
        assert all(v < 20.0 for v in corrected), f"Correction biaisée : {list(corrected)}"

    def test_theoretical_always_non_negative(self):
        """Les valeurs corrigées ne doivent jamais être négatives."""
        units = [1.0] * 5 + [0.0] * 10
        stocks = [5] * 5 + [0] * 10
        df = make_df(units, stocks)
        result = correct_out_of_stock(df)
        assert (result["theoretical_units_sold"] >= 0).all()

    def test_fallback_to_global_median(self):
        """Si toute la série est en rupture, fallback = 0."""
        units = [0.0] * 10
        stocks = [0] * 10
        df = make_df(units, stocks)
        result = correct_out_of_stock(df)
        assert (result["theoretical_units_sold"] == 0.0).all()

    def test_partial_window_at_start(self):
        """En début de série (<14j), min_periods=1 évite les NaN."""
        units = [5.0, 0.0, 0.0, 5.0, 5.0]
        stocks = [10, 0, 0, 10, 10]
        df = make_df(units, stocks)
        result = correct_out_of_stock(df)
        assert result["theoretical_units_sold"].isna().sum() == 0

    def test_missing_column_raises(self):
        """Une colonne manquante doit lever ValueError."""
        df = pd.DataFrame({"date": [date(2025, 1, 1)], "units_sold": [5.0]})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            correct_out_of_stock(df)

    def test_sorted_by_date(self):
        """Le résultat est bien trié par date croissante."""
        df = make_df([5, 3, 7, 2], [10] * 4)
        df = df.iloc[::-1].reset_index(drop=True)
        result = correct_out_of_stock(df)
        assert result["date"].is_monotonic_increasing

    def test_rolling_window_constant(self):
        """La fenêtre de 14 jours est bien définie."""
        assert ROLLING_WINDOW == 14


class TestCorrectOutOfStockBatch:

    def test_batch_two_products(self):
        """Traitement de deux produits indépendants."""
        df = pd.DataFrame({
            "product_id": ["p1"] * 5 + ["p2"] * 5,
            "date": list(pd.date_range("2025-01-01", periods=5)) * 2,
            "units_sold": [10.0] * 4 + [0.0] + [5.0] * 4 + [0.0],
            "end_of_day_stock": [100] * 4 + [0] + [100] * 4 + [0],
        })
        result = correct_out_of_stock_batch(df)
        assert set(result["product_id"].unique()) == {"p1", "p2"}
        assert "theoretical_units_sold" in result.columns
        assert "is_stockout" in result.columns

    def test_batch_missing_product_id_raises(self):
        """Colonnes manquantes → ValueError."""
        df = pd.DataFrame({"date": [], "units_sold": [], "end_of_day_stock": []})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            correct_out_of_stock_batch(df)
