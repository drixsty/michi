import pandas as pd
import numpy as np
import math
from datetime import date, timedelta

# Mock des fonctions pour la simulation
def old_reorder_qty(run_rate, lead_time, current_stock, safety_factor=1.5, moq=1):
    target = run_rate * lead_time * safety_factor
    raw_qty = max(0.0, target - current_stock)
    return math.ceil(raw_qty / moq) * moq

def new_reorder_qty(run_rate, lead_time, current_stock, sigma, service_level=0.95, moq=1):
    z_score = 1.645 # 95%
    cycle_stock = run_rate * lead_time
    safety_stock = z_score * sigma * math.sqrt(lead_time)
    target = cycle_stock + safety_stock
    raw_qty = max(0.0, target - current_stock)
    return math.ceil(raw_qty / moq) * moq

def simulate():
    print("=== Simulation Michi DS v1 vs DS v2 ===")
    print(f"Service Level: 95% (Z=1.645) | Lead Time: 14 jours | Current Stock: 50\n")
    
    lt = 14
    stock = 50
    
    # Cas 1 : Produit STABLE (Ventes régulières)
    # Demande moyenne ~10, sigma très faible
    stable_sales = [10, 11, 9, 10, 10, 11, 10, 10, 9, 11] * 3
    avg_stable = np.mean(stable_sales)
    sigma_stable = np.std(stable_sales)
    
    # Cas 2 : Produit VOLATIL (Promos, pics, aléatoire)
    # Demande moyenne ~10, sigma élevé
    volatile_sales = [0, 25, 0, 5, 40, 0, 0, 30, 0, 0] * 3
    avg_volatile = np.mean(volatile_sales)
    sigma_volatile = np.std(volatile_sales)
    
    scenarios = [
        ("Produit STABLE", avg_stable, sigma_stable),
        ("Produit VOLATIL", avg_volatile, sigma_volatile),
    ]
    
    header = f"{'Scénario':<20} | {'Moyenne':<8} | {'Sigma':<8} | {'Ancien (1.5x)':<15} | {'Nouveau (95%)':<15} | {'Diff'}"
    print(header)
    print("-" * len(header))
    
    for name, avg, sig in scenarios:
        old_q = old_reorder_qty(avg, lt, stock)
        new_q = new_reorder_qty(avg, lt, stock, sig)
        diff = new_q - old_q
        print(f"{name:<20} | {avg:<8.2f} | {sig:<8.2f} | {old_q:<15.0f} | {new_q:<15.0f} | {diff:+.0f}")

    print("\nConclusion :")
    print("- Sur le produit STABLE, l'ancien modèle sur-stocke inutilement car il ignore la faible variance.")
    print("- Sur le produit VOLATIL, l'ancien modèle sous-estime le risque de rupture car la variance est élevée.")

if __name__ == "__main__":
    simulate()
