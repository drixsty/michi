---
id: audit-s21
title: Audit Technique & Planning
sidebar_label: 🔍 Audit S21
---

# Audit Technique & Sprint Planning — Sprint 21

Ce document résume l'audit technique réalisé avant le lancement du Sprint 21 et la stratégie adoptée pour corriger la dette technique.

## 1. RÉSUMÉ EXÉCUTIF

### Objectif du Sprint 21
Transformer Michi d'un monolithe modulaire vers une **architecture hexagonale robuste**, dotée d'une **documentation vivante** (Docusaurus + API docs), de **tests solides** (85% coverage) et d'un **support i18n** (FR + EN).

### Métriques cibles
| KPI | Cible Sprint 21 | Statut |
|-----|----------------|--------|
| Coverage backend | **85%** | ✅ Atteint (>85% App) |
| Coverage frontend | **60%** | ✅ Atteint |
| Resolvers GraphQL avec logique DB directe | **0** | ✅ Corrigé |
| Endpoints sans docs formelles | **0%** | ✅ Corrigé (Via ce site) |
| Support i18n | ✅ FR + EN | ✅ Done |

---

## 2. AUDIT — ÉTAT DES LIEUX

### Dette Technique Identifiée
Avant ce sprint, plusieurs problèmes freinaient la scalabilité :
1. **Fat Resolvers :** Le fichier `schema.py` contenait plus de 700 lignes avec des accès directs à la base de données.
2. **Couplage Fort :** Les services dépendaient directement des modèles SQLAlchemy, rendant les tests unitaires complexes.
3. **Typage Lâche :** Utilisation fréquente de `Any` et manque de synchronisation entre les types Backend (Strawberry) et Frontend.

### Solutions Apportées
- **Inversion de Dépendance :** Introduction de `IRepository` (Protocols) pour isoler le domaine du SQL.
- **Service Container :** Centralisation de l'injection de dépendances dans `core/di.py`.
- **GraphQL Codegen :** Synchronisation automatique des types TypeScript dans `packages/types`.

---

## 3. ÉPIQUES DU SPRINT

- **EPIC A :** Monorepo & Restructuration (npm workspaces).
- **EPIC B :** Architecture DDD Hexagonale (Refactoring complet du backend).
- **EPIC C :** Typage Strict (Mypy --strict & TSC --strict).
- **EPIC D :** Documentation (Docusaurus + AI Documentation).

---

:::caution Risques Migrés
Le risque majeur de ce sprint était la casse des imports lors du passage en monorepo (`apps/api/`). Grâce à une suite de tests unitaires complète lancée en CI/CD, ce risque a été minimisé.
:::
