---
id: forecasting-pipeline
title: Pipeline Forecasting
sidebar_label: Pipeline Forecasting
slug: /architecture/forecasting-pipeline
---

# Pipeline de Prévision

## Vue d'ensemble

```
données brutes (ventes + stocks)
    │
    1. OOS Correction     → corrige les jours de rupture
    │
    2. IQR Detection      → détecte les outliers (borne haute uniquement)
    │
    3. Run Rate           → calcule le taux de vente journalier adaptatif
    │
    4. Predictions        → date de rupture + quantité de réassort
    │
    5. ABC Analysis       → rang A/B/C par profit annuel
```

## 1. Correction OOS

**Formule :** pour chaque jour `j` avec `end_of_day_stock = 0` :

```
theoretical_units_sold[j] = median(units_sold[j-14..j-1] où stock > 0)
```

Si < 4 jours disponibles → médiane globale de la série.

## 2. Détection IQR (borne haute uniquement)

```
Q3 = 75e percentile (fenêtre glissante 11j, centrée)
IQR = Q3 - Q1
borne_haute = Q3 + 1.5 × IQR

outlier si units_sold > borne_haute AND NOT stockout
```

:::info
Seule la borne haute est utilisée. Les valeurs basses représentent une vraie faible demande — les flaguer comme outliers génère des faux positifs.
:::

## 3. Run Rate adaptatif

```python
# Momentum = short_term_7j / medium_term_30j
# Si momentum > 1.2 (croissance > 20%) → fenêtre 7j (réactivité)
# Sinon → fenêtre 30j (stabilité)

run_rate = median(corrected_units_sold, window=adaptive)
```

## 4. Prédictions

```
predicted_stockout_date = today + (current_stock / run_rate)
reorder_quantity = run_rate × lead_time × safety_factor
```

## Métriques MAPE (seuils qualité)

| Test | Seuil |
|------|-------|
| Pipeline combiné | ≤ 15% |
| OOS seul | ≤ 25% |
| IQR seul | ≤ 20% |
