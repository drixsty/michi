import pandas as pd
import os
from datetime import datetime, timedelta

# Dossier de destination
output_dir = "apps/api/tests/data"
os.makedirs(output_dir, exist_ok=True)

def generate_anomalies():
    # 1. Anomalies (Z-Score)
    data = {
        "sku": ["IPHONE-15"] * 10,
        "date": [(datetime(2026, 4, 1) + timedelta(days=i)).strftime("%d/%m/%Y") for i in range(10)],
        "vendu": [5, 4, 6, 5, 5, 500, 4, 5, 6, 5], # 500 est l'anomalie
        "stock": [100] * 10
    }
    pd.DataFrame(data).to_csv(os.path.join(output_dir, "michi_test_anomalies.csv"), index=False)
    print("OK: michi_test_anomalies.csv genere.")

def generate_fuzzy():
    # 2. Fuzzy Matching
    data = {
        "sku": ["iphone15", "IPHONE 15", "i-phone-15", "IPHONE_15"],
        "nom": ["iPhone 15 Blue"] * 4,
        "quantite": [10, 15, 20, 25]
    }
    pd.DataFrame(data).to_csv(os.path.join(output_dir, "michi_test_fuzzy.csv"), index=False)
    print("OK: michi_test_fuzzy.csv genere.")

def generate_interpolation():
    # 3. Interpolation
    # On saute le 03/04 et le 05/04
    dates = ["01/04/2026", "02/04/2026", "04/04/2026", "06/04/2026"]
    data = {
        "sku": ["PROD-ABC"] * 4,
        "date": dates,
        "ventes": [10, 12, 15, 8],
        "stock": [50, 38, 23, 15]
    }
    pd.DataFrame(data).to_csv(os.path.join(output_dir, "michi_test_interpolation.csv"), index=False)
    print("OK: michi_test_interpolation.csv genere.")

def generate_excel():
    # 4. Excel complet
    data = {
        "Reference": ["PROD-EXCEL", "PROD-EXCEL", "PROD-EXCEL"],
        "Date Vente": ["01/04/2026", "02/04/2026", "04/04/2026"],
        "Ventes": [5, 5, 5],
        "Stock": [100, 95, 90]
    }
    pd.DataFrame(data).to_excel(os.path.join(output_dir, "michi_test_full.xlsx"), index=False)
    print("OK: michi_test_full.xlsx genere.")

if __name__ == "__main__":
    generate_anomalies()
    generate_fuzzy()
    generate_interpolation()
    generate_excel()
