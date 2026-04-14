---
id: configuration
title: Configuration
sidebar_label: Configuration
slug: /guide/configuration
---

# Configuration

## Paramètres organisation

Dans **Réglages > Organisation** :

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| `currency` | Devise affichée (€, $, £) | `€` |
| `is_mutualized` | Agrégation omnicanale | `false` |

## Algorithmes de prévision

Seuils configurables dans `backend/src/modules/intelligence/algorithms/` :

| Constante | Fichier | Valeur | Description |
|-----------|---------|--------|-------------|
| `RUN_RATE_WINDOW` | `run_rate.py` | 30 jours | Fenêtre médiane glissante |
| `OUTLIER_ROLLING_WINDOW` | `outlier_detection.py` | 11 jours | Fenêtre IQR centrée |
| `OOS_CORRECTION_WINDOW` | `out_of_stock_correction.py` | 14 jours | Correction ruptures |

## Seuils de qualité (MAPE)

| Pipeline | Seuil | Fichier |
|----------|-------|---------|
| Combiné | 15% | `test_mape.py` |
| OOS seul | 25% | `test_mape.py` |
| IQR seul | 20% | `test_mape.py` |

## Health Score — Pondération 3PI

```
health_score = avail × 0.5 + rot × 0.3 + out_ratio × 0.2
```

- **avail** : disponibilité CA (1 - revenue_at_risk / total_potential)
- **rot** : rotation stock (optimal 7j–45j)
- **out_ratio** : taux non-rupture
