import os
import sys
import asyncio
from datetime import date, timedelta
from loguru import logger

# Add backend/src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from modules.forecasting.algorithms.out_of_stock_correction import correct_out_of_stock
from modules.forecasting.algorithms.outlier_detection import detect_outliers
from modules.forecasting.algorithms.run_rate import calculate_run_rate_batch

def generate_tough_data(days=395, sigma_ratio=0.6):
    """
    Génère des données simulant la réalité e-commerce :
    - Tendance haussière
    - Saisonnalité hebdomadaire
    - Bruit très élevé (volatilité)
    - Ruptures de stock
    """
    dates = [date(2023, 1, 1) + timedelta(days=i) for i in range(days)]
    
    # Base de vente (10 u/jour) avec tendance +20% / an
    base_sales = np.linspace(10, 12, days)
    
    # Saisonnalité hebdo (ventes +50% le weekend)
    weekly_pattern = np.array([1.0, 1.0, 1.0, 1.0, 1.2, 1.5, 1.3] * (days // 7 + 1))[:days]
    
    # Bruit gaussien fort
    noise = np.random.normal(0, base_sales * sigma_ratio, days)
    
    sales = base_sales * weekly_pattern + noise
    sales = np.maximum(0, np.round(sales))
    
    # Simulation de ruptures (0 stock pendant 10 jours)
    sales[200:210] = 0
    is_stockout = [False] * days
    for i in range(200, 210): is_stockout[i] = True
    
    # Michi algorithms expect 'units_sold' and 'end_of_day_stock'
    df = pd.DataFrame({
        "date": dates,
        "units_sold": sales,
        "end_of_day_stock": [0 if s else 10 for s in is_stockout],
        "is_stockout": is_stockout
    })
    return df

async def validate_mape():
    logger.info("🚀 [Validation MAPE] Démarrage sur données haute volatilité...")
    
    # 1. Génération
    df = generate_tough_data()
    df = df.rename(columns={"raw_units_sold": "units_sold"})
    # Simuler le stock pour correspondre aux jours de rupture
    df["end_of_day_stock"] = df["is_stockout"].apply(lambda x: 0 if x else 10)
    
    # Séparation Train (365 j) / Test (30 j)
    df_train = df.iloc[:365].copy()
    df_test = df.iloc[365:].copy()
    
    # 2. Nettoyage
    logger.info("🧹 Nettoyage des données (OOS + IQR)...")
    df_train = correct_out_of_stock(df_train)
    
    # detect_outliers attend le DataFrame complet
    # Il utilise 'theoretical_units_sold' s'il existe
    df_train = detect_outliers(df_train)
    
    # 3. Prédiction (Run Rate)
    logger.info("📈 Calcul du Run Rate...")
    df_train["product_id"] = "test-sku"
    # calculate_run_rate_batch attend [product_id, date, corrected_units_sold]
    # La colonne produite par detect_outliers est 'corrected_units_sold'
    df_run = calculate_run_rate_batch(df_train)
    predicted_run_rate = df_run.iloc[-1]["run_rate"]
    
    # 4. Évaluation
    # On compare le run_rate prédit avec la moyenne réelle des 30 jours suivants
    actual_mean = df_test["raw_units_sold"].mean()
    
    error = abs(predicted_run_rate - actual_mean)
    mape = (error / actual_mean) * 100
    
    logger.info("--- RÉSULTATS ---")
    logger.info(f"Produit : SKU-TOUGH (Volatilité 60%)")
    logger.info(f"Moyenne Réelle (Next 30d) : {actual_mean:.2f} u./jour")
    logger.info(f"Run Rate Prédit (Michi) : {predicted_run_rate:.2f} u./jour")
    logger.info(f"ERREUR MAPE : {mape:.2f}%")
    
    if mape < 20:
        logger.success("✅ VALIDATION RÉUSSIE (MAPE < 20%)")
    else:
        logger.warning("⚠️ ATTENTION : MAPE élevé. Vérification des paramètres recommandée.")

if __name__ == "__main__":
    asyncio.run(validate_mape())
