import pandas as pd
"""
Seasonality Algorithm (Sprint 15)
Persona: #2 Data Scientist / ML Engineer

Détection automatique de la saisonnalité pour ajuster le Run Rate.
L'objectif est de comparer la demande actuelle (court terme) avec la tendance historique.

Note : En phase MVP, si l'historique est < 14 jours, on retourne 1.0.
Sinon, on utilise une décomposition simple pour identifier si nous sommes dans une phase 
ascendante ou descendante du cycle saisonnier hebdomadaire/mensuel.
"""

def detect_seasonality_factor(df: pd.DataFrame, window: int = 14) -> float:
    """
    Calcule un facteur de boost saisonnier basé sur l'évolution récente de la demande.
    (Momentum court terme vs moyen terme).
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


def calculate_weekly_indices(df: pd.DataFrame) -> dict[int, float]:
    """
    Calcule les index saisonniers par jour de la semaine (0=Lundi, 6=Dimanche).
    
    L'index est normalisé pour que la moyenne soit de 1.0.
    Un index de 1.2 le samedi signifie que le samedi vend 20% de plus que la moyenne.
    """
    if df.empty or len(df) < 28: # Besoin d'au moins 4 semaines pour un index fiable
        return {i: 1.0 for i in range(7)}

    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
        
    df['day_of_week'] = df['date'].dt.dayofweek
    
    # Calcul de la moyenne par jour de la semaine
    daily_avg = df.groupby('day_of_week')['corrected_units_sold'].mean()
    global_avg = daily_avg.mean()
    
    if global_avg <= 0:
        return {i: 1.0 for i in range(7)}
        
    indices = (daily_avg / global_avg).to_dict()
    
    # S'assurer que tous les jours sont présents
    for i in range(7):
        if i not in indices:
            indices[i] = 1.0
            
    return indices


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
