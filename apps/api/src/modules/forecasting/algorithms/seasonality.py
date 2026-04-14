"""
Seasonality Algorithm (Sprint 15)
Persona: #2 Data Scientist / ML Engineer

Détection automatique de la saisonnalité pour ajuster le Run Rate.
L'objectif est de comparer la demande actuelle (court terme) avec la tendance historique.

Note : En phase MVP, si l'historique est < 14 jours, on retourne 1.0.
Sinon, on utilise une décomposition simple pour identifier si nous sommes dans une phase 
ascendante ou descendante du cycle saisonnier hebdomadaire/mensuel.
"""
import pandas as pd
import numpy as np
from loguru import logger

def detect_seasonality_factor(df: pd.DataFrame, window: int = 14) -> float:
    """
    Calcule un facteur de boost saisonnier basé sur l'évolution récente de la demande.
    
    Args:
        df: DataFrame de demande avec [date, corrected_units_sold]
        window: Fenêtre de comparaison
        
    Returns:
        float: Facteur multiplicateur (ex: 1.2 pour +20% de demande saisonnière détectée)
    """
    if df.empty or len(df) < window * 2:
        return 1.0

    df = df.sort_values('date')
    
    # On compare la moyenne des 7 derniers jours avec la moyenne des 30 derniers jours
    recent_avg = df['corrected_units_sold'].tail(7).mean()
    historical_avg = df['corrected_units_sold'].tail(30).mean()
    
    if historical_avg <= 0:
        return 1.0
        
    factor = recent_avg / historical_avg
    
    # Capage par sécurité pour éviter des prédictions délirantes (entre 0.5 et 2.5)
    factor = max(0.5, min(2.5, factor))
    
    # On ne renvoie un boost significatif que si l'écart est supérieur à 10%
    if 0.9 <= factor <= 1.1:
        return 1.0
        
    return float(factor)

def apply_seasonality_batch(products_df: pd.DataFrame, history_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique la détection de saisonnalité à une liste de produits.
    """
    factors = {}
    for pid in products_df['product_id'].unique():
        prod_history = history_df[history_df['product_id'] == pid]
        factors[pid] = detect_seasonality_factor(prod_history)
        
    products_df['seasonality_factor'] = products_df['product_id'].map(factors)
    return products_df
