---
id: overview
title: Vue d'ensemble architecture
sidebar_label: Vue d'ensemble
slug: /architecture/overview
---

# Architecture Michi 道

## Stack technique

| Couche | Technologie |
|--------|-------------|
| **Backend** | Python 3.12, FastAPI, Strawberry GraphQL |
| **ORM** | SQLAlchemy 2.0 Async + Asyncpg |
| **Migrations** | Alembic |
| **Frontend** | Next.js 14 App Router, Apollo Client, Tailwind CSS |
| **Base de données** | PostgreSQL 15 |
| **Cache** | Redis 7 |
| **Tests** | pytest + Playwright + Vitest |

## Flux global

```
Frontend (Next.js 14)
    │ HTTPS / GraphQL
    ▼
FastAPI + Strawberry GraphQL  (/graphql)
    │
    ▼
Application Services (DDD)
    │           │
    ▼           ▼
Infrastructure  Intelligence/
(SQLAlchemy)   (Algorithmes purs)
    │
    ▼
PostgreSQL 15
```

## Modules backend

| Module | Responsabilité |
|--------|----------------|
| `auth/` | Authentification JWT, OAuth Google, RBAC |
| `inventory/` | Produits, stocks, alertes, plateformes |
| `forecasting/` | Prédictions (délègue à intelligence/) |
| `decisions/` | Centre décisionnel, KPIs financiers |
| `billing/` | Abonnements Stripe |
| `intelligence/` | Algorithmes IA + analytics (zero-dependency) |

## Voir aussi

- [Architecture DDD Hexagonale](./ddd-hexagonal)
- [Module Intelligence/](./intelligence-module)
- [Pipeline Forecasting](./forecasting-pipeline)
