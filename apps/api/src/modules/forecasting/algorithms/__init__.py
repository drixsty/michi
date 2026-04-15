"""
Algorithmes de nettoyage de la demande — re-exports vers intelligence/.

Les implémentations canoniques vivent désormais dans :
    src.modules.intelligence.algorithms

Ce module maintient la compatibilité ascendante pour tout code qui importait
depuis src.modules.forecasting.algorithms.*
"""
from modules.intelligence.algorithms import (
    calculate_run_rate,
    calculate_run_rate_batch,
    RUN_RATE_WINDOW,
    detect_outliers,
    detect_outliers_batch,
    OUTLIER_ROLLING_WINDOW,
    correct_out_of_stock,
    correct_out_of_stock_batch,
    calculate_abc_ranks_batch,
    detect_seasonality_factor,
    predict_stockout_date,
    calculate_reorder_quantity,
)

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
