---
id: intelligence-module
title: Module intelligence/
sidebar_label: Module intelligence/
slug: /architecture/intelligence-module
---

# Module `intelligence/` — Bounded Context IA

Sprint 21, US 21.30 — **Zero-dependency** : pas de SQLAlchemy, FastAPI, HTTP.

## Structure

```
intelligence/
├── algorithms/          # 6 algorithmes de prévision (Pandas)
│   ├── run_rate.py
│   ├── outlier_detection.py
│   ├── out_of_stock_correction.py
│   ├── abc_analysis.py
│   ├── seasonality.py
│   └── predictions.py
├── analytics/           # KPIs purs (primitives Python)
│   ├── financial_kpis.py   # calculate_financial_kpis()
│   ├── health_score.py     # calculate_health_score()
│   └── risk_scoring.py     # score_products()
├── pipeline/
│   └── cleaning_pipeline.py  # OOS → IQR → RunRate
├── domain/
│   ├── entities.py      # DemandSignal, PredictionResult, RiskScore
│   └── ports.py         # IIntelligenceEngine, IDemandDataPort
└── tests/               # 28 tests, 100% pass
```

## Health Score 3PI

```python
health_score = round((avail * 0.5 + rot * 0.3 + out_ratio * 0.2) * 100)
```

| Composante | Poids | Description |
|------------|-------|-------------|
| `avail` | 50% | 1 - revenue_at_risk / total_potential |
| `rot` | 30% | Rotation optimale : 7j–45j = 1.0 |
| `out_ratio` | 20% | 1 - stockout_count / total_skus |

## Pipeline de nettoyage

```
données brutes (DataFrame)
    │
    ▼ correct_out_of_stock()   → theoretical_units_sold
    │
    ▼ detect_outliers()        → corrected_units_sold (upper-bound IQR only)
    │
    ▼ calculate_run_rate()     → run_rate journalier (médiane adaptative)
```

## Vérification zero-dependency

```bash
grep -r "import sqlalchemy" backend/src/modules/intelligence/
# → 0 résultat
```
