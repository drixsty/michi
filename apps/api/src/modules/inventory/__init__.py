"""Module Inventory — DDD hexagonal (Sprint 21).
Les imports explicites ont été retirés pour éviter la double registration SQLAlchemy
quand pytest scanne src/ et que tests/conftest.py charge l'app en parallèle.
Importer directement depuis les sous-modules si nécessaire.
"""
