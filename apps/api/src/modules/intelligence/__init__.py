"""
Module intelligence/ — Bounded Context IA de Michi 道

Contient tous les algorithmes de prévision et les calculs analytiques.
Ce module est ZERO-DÉPENDANCE externe : pas de SQLAlchemy, pas de FastAPI,
pas de HTTP. Entrées : DataFrames Pandas ou primitives Python.
Sorties : valeurs typées (dataclasses ou scalaires).

Structure :
    algorithms/   — 6 algorithmes de forecasting (fonctions pures)
    analytics/    — calculs BI (health score, KPIs financiers, risk scoring)
    pipeline/     — orchestration nettoyage pure (OOS -> IQR -> RunRate)
    domain/       — entités et ports (Protocols)
    tests/        — suite de tests isolée
"""
