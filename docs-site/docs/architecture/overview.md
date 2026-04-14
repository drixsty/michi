---
id: overview
title: Vue d'Ensemble
sidebar_label: 🏛️ Vue d'Ensemble
sidebar_position: 1
---

# Vue d'Ensemble Architecture

## 1. Architecture Globale

Michi 道 utilise une architecture moderne découplée, optimisée pour la performance et la scalabilité.

```mermaid
graph TD
    subgraph Frontend
        WEB[Next.js 14 App Router]
        APOLLO[Apollo Client]
    end

    subgraph Backend
        FAST[FastAPI Gateway]
        STRAW[Strawberry GraphQL]
        
        subgraph Modules
            AUTH[Auth Module]
            INV[Inventory Module]
            FORE[Forecasting Module]
            SUP[Suppliers Module]
        end
    end

    subgraph Persistence
        PG[(PostgreSQL 15)]
        REDIS[(Redis Cache / Queue)]
    end

    WEB -->|GraphQL| FAST
    FAST --> STRAW
    STRAW --> AUTH
    STRAW --> INV
    STRAW --> FORE
    STRAW --> SUP
    
    Modules --> PG
    FORE --> REDIS
```

### 1.1 Stack Technique
- **Backend :** Python 3.12, FastAPI, Strawberry, SQLAlchemy 2.0 (Async).
- **Frontend :** TypeScript, Next.js 14, Apollo Client, Tailwind CSS, shadcn/ui.
- **Infrastructure :** Docker, PostgreSQL, Redis.

### 1.2 Schéma Relationnel (ERD)

L'architecture de données de Michi est conçue pour le multi-tenancy (SaaS) avec une isolation forte par organisation.

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : contains
    ORGANIZATION ||--o{ STORE : owns
    STORE ||--o{ PRODUCT : aggregates
    STORE ||--o{ SALES_LOG : has
    PRODUCT ||--o{ CLEANED_DEMAND : generates
    PRODUCT ||--o{ PREDICTION : has
    PRODUCT ||--o{ ALERT : triggers

    ORGANIZATION {
        uuid id PK
        string name
        string slug
        string plan
    }

    USER {
        uuid id PK
        string email
        string first_name
        string last_name
    }

    PRODUCT {
        uuid id PK
        string sku
        string title
        int current_stock
        float lead_time
    }

    PREDICTION {
        uuid id PK
        float run_rate
        date predicted_stockout_date
        int reorder_quantity
    }
```

### 1.3 Principes Clés
1. **Modularity (DDD) :** Chaque domaine métier est isolé.
2. **API-First (GraphQL) :** Un contrat unique et typé.
3. **Stateless :** Authentification JWT, pas de sessions côté serveur.
4. **Async-Everywhere :** Utilisation intensive de `async/await` pour la performance I/O.
