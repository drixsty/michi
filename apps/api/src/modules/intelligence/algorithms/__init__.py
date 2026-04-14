"""
Algorithmes de forecasting — réexports publics du module intelligence.
"""
from .run_rate import calculate_run_rate, calculate_run_rate_batch, RUN_RATE_WINDOW
from .outlier_detection import detect_outliers, detect_outliers_batch, OUTLIER_ROLLING_WINDOW
from .out_of_stock_correction import correct_out_of_stock, correct_out_of_stock_batch
from .abc_analysis import calculate_abc_ranks_batch
from .seasonality import detect_seasonality_factor
from .predictions import predict_stockout_date, calculate_reorder_quantity

__all__ = [
    "calculate_run_rate",
    "calculate_run_rate_batch",
    "RUN_RATE_WINDOW",
    "detect_outliers",
    "detect_outliers_batch",
    "OUTLIER_ROLLING_WINDOW",
    "correct_out_of_stock",
    "correct_out_of_stock_batch",
    "calculate_abc_ranks_batch",
    "detect_seasonality_factor",
    "predict_stockout_date",
    "calculate_reorder_quantity",
]
