"""
Tests unitaires — intelligence/pipeline/cleaning_pipeline.py
"""
import pytest
import pandas as pd
import numpy as np  # noqa: F401
from src.modules.intelligence.pipeline.cleaning_pipeline import run_cleaning_pipeline


def _make_df(n: int = 30, units: float = 5.0, stock: int = 10) -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n),
        "units_sold": [units] * n,
        "end_of_day_stock": [stock] * n,
    })


class TestCleaningPipeline:
    def test_returns_dataframe_and_float(self) -> None:
        df = _make_df()
        result_df, run_rate = run_cleaning_pipeline(df, sku="SKU001")
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(run_rate, float)

    def test_run_rate_positive_on_valid_data(self) -> None:
        df = _make_df(n=40, units=5.0)
        _, run_rate = run_cleaning_pipeline(df)
        assert run_rate > 0

    def test_corrected_quantity_column_present(self) -> None:
        df = _make_df()
        result_df, _ = run_cleaning_pipeline(df)
        assert "corrected_quantity" in result_df.columns

    def test_oos_correction_applied(self) -> None:
        df = _make_df(n=30, units=5.0, stock=10)
        df.loc[28:, "end_of_day_stock"] = 0
        df.loc[28:, "units_sold"] = 0
        result_df, _ = run_cleaning_pipeline(df)
        assert "theoretical_units_sold" in result_df.columns

    def test_missing_columns_raises(self) -> None:
        bad_df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=5)})
        with pytest.raises(ValueError, match="colonnes manquantes"):
            run_cleaning_pipeline(bad_df)

    def test_outlier_column_present(self) -> None:
        df = _make_df(n=40)
        result_df, _ = run_cleaning_pipeline(df)
        assert "is_outlier" in result_df.columns

    def test_iqr_lower_present_for_backward_compat(self) -> None:
        df = _make_df(n=40)
        result_df, _ = run_cleaning_pipeline(df)
        assert "iqr_lower" in result_df.columns
