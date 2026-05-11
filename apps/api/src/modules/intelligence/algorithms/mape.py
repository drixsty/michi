"""
MAPE Calculation Algorithm
Calculates the Mean Absolute Percentage Error for a prediction.
"""
import pandas as pd
import numpy as np

def calculate_mape_score(run_rate: float, recent_sales: pd.Series) -> float:
    """
    Calcule le score MAPE en comparant le run_rate (prédiction moyenne)
    avec la moyenne des ventes réelles récentes.
    """
    if recent_sales.empty:
        return 0.0
    
    actual_avg = recent_sales.mean()
    if actual_avg <= 0:
        return 0.0
        
    mape = abs(run_rate - actual_avg) / actual_avg
    return float(min(1.0, mape)) # Capped at 1.0 (100% error)
