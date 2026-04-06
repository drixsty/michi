# Architecture Technique Détaillée - Michi 道

**Version:** 2.0  
**Date:** Mars 2026  
**Tech Lead:** [Votre Nom]  
**Stack:** Python 3.11+, FastAPI, Strawberry GraphQL, PostgreSQL 15+, Next.js 14

---

## Table des Matières

1. [Vue d'Ensemble Architecture](#1-vue-densemble-architecture)
2. [Schéma de Base de Données](#2-schéma-de-base-de-données)
3. [API GraphQL (Schema First)](#3-api-graphql-schema-first)
4. [Architecture Backend (Domain-Driven)](#4-architecture-backend-domain-driven)
5. [Pipeline Data Science](#5-pipeline-data-science)
6. [Architecture Frontend](#6-architecture-frontend)
7. [Sécurité & Performance](#7-sécurité--performance)
8. [Déploiement & Infrastructure](#8-déploiement--infrastructure)
9. [Testing Strategy](#9-testing-strategy)
10. [Décisions Techniques (ADR)](#10-décisions-techniques-adr)

---

## 1. Vue d'Ensemble Architecture

### 1.1 Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│  Next.js 14 (App Router) + Apollo Client + Tailwind CSS   │
│              Déployé sur Vercel Edge Network                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTPS (GraphQL)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY                            │
│        FastAPI + Strawberry GraphQL (/graphql)             │
│              Middleware: JWT Auth, CORS, Rate Limit         │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴──────────┬─────────────────┐
         ▼                      ▼                 ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│  AUTH MODULE    │  │ INVENTORY MODULE│  │ FORECAST MODULE  │
│  (JWT, Users)   │  │ (Unified model) │  │ (Algorithms,     │
└────────┬────────┘  └────────┬────────┘  │  Simulations)    │
         │                    │           └────────┬─────────┘
         │          ┌─────────┴─────────┐          │
         │          ▼                   ▼          │
         │  ┌────────────────┐  ┌────────────────┐ │
         │  │ INGESTION MOD. │  │ SUPPLIERS MOD. │ │
         │  │ (Connectors)   │  │ (Lead Times)   │ │
         │  └────────────────┘  └────────────────┘ │
         └────────────────────┬─────────────────────┘
                              │
                              ▼
         ┌──────────────────────────────────────────┐
         │      PostgreSQL 15+ (Primary DB)         │
         │  Tables: users, products, daily_sales,   │
         │          cleaned_demand, suppliers       │
         └──────────────────────────────────────────┘
```

### 1.2 Principes Architecturaux

**1. Modularity (Domain-Driven Design)**
- Chaque module business est isolé dans son propre dossier
- Pas de dépendances circulaires entre modules
- Chaque module expose son API via GraphQL resolvers

**2. API-First (GraphQL)**
- Un seul endpoint `/graphql` pour toutes les opérations
- Schema-first approach (définir le schema GraphQL avant le code)
- Pas de REST endpoints (sauf health check)

**3. Separation of Concerns**
- **Backend :** Business logic, algorithmes, persistence
- **Frontend :** Présentation, UX, validations côté client
- **Data Science :** Pipeline isolé, testable indépendamment

**4. Scalability**
- Architecture stateless (JWT, pas de sessions serveur)
- Async Python (FastAPI + SQLAlchemy 2.0 Async)
- Prêt pour horizontal scaling (multi-instances)

---

## 2. Schéma de Base de Données

### 2.1 ERD (Entity-Relationship Diagram)

```
┌─────────────────┐
│     USERS       │
├─────────────────┤
│ id (UUID, PK)   │──┐
│ email (String)  │  │
│ hashed_password │  │
│ shop_id (UUID)  │  │ 1:N
│ created_at      │  │
└─────────────────┘  │
                     │
                     ▼
┌─────────────────────────────────────────┐
│              PRODUCTS                   │
├─────────────────────────────────────────┤
│ id (UUID, PK)                           │──┐
│ shop_id (UUID, FK → users)              │  │
│ sku (String, unique per shop)           │  │
│ title (String)                          │  │
│ current_inventory (Int)                 │  │ 1:N
│ lead_time_days (Int, default=14)        │  │
│ moq (Int, default=1)                    │  │
│ created_at, updated_at                  │  │
└─────────────────────────────────────────┘  │
                                              │
                     ┌────────────────────────┘
                     │
                     ▼
┌───────────────────────────────────────────────┐
│           DAILY_SALES_LOGS                    │
├───────────────────────────────────────────────┤
│ id (UUID, PK)                                 │
│ product_id (UUID, FK → products)              │
│ date (Date)                                   │
│ units_sold (Int)                              │
│ end_of_day_stock (Int)                        │
│ created_at                                    │
│                                               │
│ UNIQUE CONSTRAINT (product_id, date)          │
└───────────────────────────────────────────────┘
                     │
                     │ Traité par algorithme
                     ▼
┌───────────────────────────────────────────────┐
│           CLEANED_DEMAND                      │
├───────────────────────────────────────────────┤
│ id (UUID, PK)                                 │
│ product_id (UUID, FK → products)              │
│ date (Date)                                   │
│ theoretical_units_sold (Float)                │
│ is_outlier (Boolean)                          │
│ created_at                                    │
│                                               │
│ UNIQUE CONSTRAINT (product_id, date)          │
└───────────────────────────────────────────────┘
```

### 2.2 Tables Détaillées (PostgreSQL DDL)

```sql
-- Extension pour UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    shop_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_shop_id ON users(shop_id);
CREATE INDEX idx_users_email ON users(email);

-- Table products
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shop_id UUID NOT NULL,
    sku VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    current_inventory INT NOT NULL DEFAULT 0,
    lead_time_days INT NOT NULL DEFAULT 14,
    moq INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_inventory CHECK (current_inventory >= 0),
    CONSTRAINT check_lead_time CHECK (lead_time_days > 0 AND lead_time_days <= 90),
    CONSTRAINT check_moq CHECK (moq > 0),
    CONSTRAINT unique_sku_per_shop UNIQUE (shop_id, sku)
);

CREATE INDEX idx_products_shop_id ON products(shop_id);
CREATE INDEX idx_products_sku ON products(shop_id, sku);

-- Table daily_sales_logs (historique brut)
CREATE TABLE daily_sales_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    units_sold INT NOT NULL DEFAULT 0,
    end_of_day_stock INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_units_sold CHECK (units_sold >= 0),
    CONSTRAINT check_stock CHECK (end_of_day_stock >= 0),
    CONSTRAINT unique_product_date UNIQUE (product_id, date)
);

CREATE INDEX idx_daily_sales_product_date ON daily_sales_logs(product_id, date DESC);

-- Table cleaned_demand (après nettoyage algorithme)
CREATE TABLE cleaned_demand (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    theoretical_units_sold FLOAT NOT NULL,
    is_outlier BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_theoretical_sold CHECK (theoretical_units_sold >= 0),
    CONSTRAINT unique_cleaned_product_date UNIQUE (product_id, date)
);

CREATE INDEX idx_cleaned_demand_product_date ON cleaned_demand(product_id, date DESC);

-- Trigger pour updated_at automatique
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 2.3 Stratégie d'Index

**Principes :**
- Index sur clés étrangères (FK) pour les JOINs
- Index composites pour les requêtes fréquentes (shop_id + sku)
- Index DESC sur dates pour tri chronologique inverse

**Queries Optimisées :**
```sql
-- Query 1 : Récupérer produits d'un shop (O(log n))
SELECT * FROM products WHERE shop_id = $1;
-- Index utilisé : idx_products_shop_id

-- Query 2 : Historique ventes d'un produit (O(log n))
SELECT * FROM daily_sales_logs 
WHERE product_id = $1 
ORDER BY date DESC 
LIMIT 365;
-- Index utilisé : idx_daily_sales_product_date

-- Query 3 : Données nettoyées pour prédictions (O(log n))
SELECT * FROM cleaned_demand 
WHERE product_id = $1 
ORDER BY date DESC 
LIMIT 90;
-- Index utilisé : idx_cleaned_demand_product_date
```

---

## 3. API GraphQL (Schema First)

### 3.1 Schema GraphQL Complet

```graphql
# ============================================
# SCALARS
# ============================================
scalar DateTime
scalar Date

# ============================================
# TYPES
# ============================================

type User {
  id: ID!
  email: String!
  shopId: ID!
  createdAt: DateTime!
}

type Product {
  id: ID!
  shopId: ID!
  sku: String!
  title: String!
  currentInventory: Int!
  leadTimeDays: Int!
  moq: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
  
  # Champs calculés (via resolvers)
  runRate: Float
  stockoutDate: Date
  recommendedOrderQty: Int
  status: ProductStatus!
}

enum ProductStatus {
  URGENT      # < 7 jours avant rupture
  WARNING     # 7-30 jours
  HEALTHY     # > 30 jours
  UNKNOWN     # Pas assez de données
}

type Alert {
  product: Product!
  stockoutDate: Date!
  daysUntilStockout: Int!
  recommendedOrderQty: Int!
  estimatedRevenueLoss: Float!
}

type KPIs {
  totalRevenueLoss: Float!
  urgentProducts: Int!
  totalProducts: Int!
}

# ============================================
# INPUTS
# ============================================

input LoginInput {
  email: String!
  password: String!
}

input UpdateInventoryRulesInput {
  productId: ID!
  leadTimeDays: Int
  moq: Int
}

# ============================================
# QUERIES
# ============================================

type Query {
  """
  Récupère l'utilisateur actuellement authentifié
  Nécessite : JWT token valide
  """
  me: User!
  
  """
  Liste tous les produits de l'utilisateur avec pagination
  Tri par défaut : Date de rupture ASC (plus urgent en premier)
  """
  products(
    limit: Int = 50
    offset: Int = 0
    status: ProductStatus
  ): [Product!]!
  
  """
  Récupère les alertes de réassort triées par urgence
  Retourne uniquement les produits nécessitant une action
  """
  replenishmentAlerts: [Alert!]!
  
  """
  KPIs pour le dashboard (cartes en haut)
  """
  dashboardKPIs: KPIs!
}

# ============================================
# MUTATIONS
# ============================================

type Mutation {
  """
  Authentification utilisateur
  Retourne un JWT token valide 24h
  """
  login(input: LoginInput!): AuthPayload!
  
  """
  Met à jour les règles d'inventaire d'un produit
  Recalcule automatiquement les prédictions
  """
  updateProductInventoryRules(input: UpdateInventoryRulesInput!): Product!
  
  """
  Déclenche la génération de données de test (Mock Shopify)
  Utilisé pour l'onboarding et les tests
  """
  triggerMockDataSync(daysToGenerate: Int!): Boolean!
  
  """
  Déclenche le pipeline de nettoyage des données
  Recalcule cleaned_demand pour tous les produits
  """
  triggerDataCleaning: Boolean!
}

# ============================================
# AUTH PAYLOAD
# ============================================

type AuthPayload {
  token: String!
  user: User!
}
```

### 3.2 Exemples de Requêtes

#### Query : Récupérer les produits urgents
```graphql
query GetUrgentProducts {
  products(status: URGENT, limit: 10) {
    id
    sku
    title
    currentInventory
    stockoutDate
    recommendedOrderQty
    status
  }
}
```

**Réponse :**
```json
{
  "data": {
    "products": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "sku": "RB-001",
        "title": "Robe Été Fleurie",
        "currentInventory": 3,
        "stockoutDate": "2026-03-08",
        "recommendedOrderQty": 100,
        "status": "URGENT"
      }
    ]
  }
}
```

#### Mutation : Login
```graphql
mutation Login {
  login(input: {
    email: "sophie@lagarde-robe.fr"
    password: "SecurePassword123!"
  }) {
    token
    user {
      id
      email
      shopId
    }
  }
}
```

#### Mutation : Mettre à jour Lead Time
```graphql
mutation UpdateLeadTime {
  updateProductInventoryRules(input: {
    productId: "550e8400-e29b-41d4-a716-446655440000"
    leadTimeDays: 21
  }) {
    id
    leadTimeDays
    stockoutDate  # Recalculé automatiquement
    recommendedOrderQty  # Recalculé automatiquement
  }
}
```

### 3.3 Resolvers (Python Strawberry)

```python
# backend/src/core/graphql/schema.py
import strawberry
from typing import List, Optional
from datetime import datetime, date

@strawberry.type
class User:
    id: strawberry.ID
    email: str
    shop_id: strawberry.ID
    created_at: datetime

@strawberry.type
class Product:
    id: strawberry.ID
    shop_id: strawberry.ID
    sku: str
    title: str
    current_inventory: int
    lead_time_days: int
    moq: int
    
    @strawberry.field
    async def run_rate(self, info) -> Optional[float]:
        """Calcule le run rate à partir de cleaned_demand"""
        forecast_service = info.context.forecast_service
        return await forecast_service.get_run_rate(self.id)
    
    @strawberry.field
    async def stockout_date(self, info) -> Optional[date]:
        """Date de rupture prévue"""
        forecast_service = info.context.forecast_service
        return await forecast_service.calculate_stockout_date(self.id)
    
    @strawberry.field
    async def recommended_order_qty(self, info) -> Optional[int]:
        """Quantité recommandée à commander"""
        forecast_service = info.context.forecast_service
        return await forecast_service.calculate_order_quantity(self.id)

@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info) -> User:
        user_id = info.context.user_id  # Extrait du JWT par middleware
        user_service = info.context.user_service
        return await user_service.get_user_by_id(user_id)
    
    @strawberry.field
    async def products(
        self,
        info,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Product]:
        shop_id = info.context.shop_id
        product_service = info.context.product_service
        return await product_service.get_products(
            shop_id=shop_id,
            limit=limit,
            offset=offset,
            status=status
        )

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def login(self, info, input: LoginInput) -> AuthPayload:
        auth_service = info.context.auth_service
        return await auth_service.login(input.email, input.password)
```

---

## 4. Architecture Backend (Domain-Driven)

### 4.1 Structure des Dossiers

```
backend/
├── src/
│   ├── core/                    # Infrastructure partagée
│   │   ├── __init__.py
│   │   ├── config.py            # Variables d'environnement, settings
│   │   ├── database.py          # Connexion async PostgreSQL
│   │   ├── security.py          # JWT, hashing password
│   │   ├── middleware/
│   │   │   ├── auth.py          # Middleware JWT
│   │   │   ├── cors.py
│   │   │   └── rate_limit.py
│   │   └── graphql/
│   │       ├── schema.py        # Schema Strawberry principal
│   │       └── context.py       # Context GraphQL (injection services)
│   │
│   ├── modules/                 # Domaines métier
│   │   ├── auth/
│   │   ├── ingestion/           # Connecteurs (CSV, Shopify, Amazon)
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Connector Interface
│   │   │   ├── shopify.py       # Shopify Logic
│   │   │   ├── csv.py           # Universal CSV Logic
│   │   │   └── service.py       # Ingestion Orchestrator
│   │   │
│   │   ├── suppliers/           # Gestion Fournisseurs
│   │   │   ├── models.py        # Supplier Table
│   │   │   └── service.py       # Delay tracking
│   │   │
│   │   ├── inventory/           # Gestion produits Agnostique
│   │   └── forecasting/         # Prédictions & Simulations
│   │
│   ├── main.py                  # FastAPI app entry point
│   └── alembic/                 # Migrations DB
│       ├── versions/
│       └── env.py
│
├── tests/                       # Tests e2e
│   ├── conftest.py
│   └── test_graphql_e2e.py
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

### 4.2 Exemple : ProductService

```python
# backend/src/modules/inventory/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from .models import Product
from ..forecasting.service import ForecastService

class ProductService:
    def __init__(self, db_session: AsyncSession, forecast_service: ForecastService):
        self.db = db_session
        self.forecast_service = forecast_service
    
    async def get_products(
        self,
        shop_id: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Product]:
        """
        Récupère les produits avec tri par urgence
        """
        query = select(Product).where(Product.shop_id == shop_id)
        
        # Filtrer par statut si demandé
        if status:
            # Calcul du statut via forecast_service
            products = await self.db.execute(query)
            products = products.scalars().all()
            
            filtered = []
            for product in products:
                product_status = await self._calculate_status(product)
                if product_status == status:
                    filtered.append(product)
            
            return filtered[offset:offset+limit]
        
        # Sinon, retourner tous les produits
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_inventory_rules(
        self,
        product_id: str,
        lead_time_days: Optional[int] = None,
        moq: Optional[int] = None
    ) -> Product:
        """
        Met à jour les règles d'inventaire d'un produit
        """
        query = select(Product).where(Product.id == product_id)
        result = await self.db.execute(query)
        product = result.scalar_one()
        
        if lead_time_days is not None:
            product.lead_time_days = lead_time_days
        
        if moq is not None:
            product.moq = moq
        
        await self.db.commit()
        await self.db.refresh(product)
        
        return product
    
    async def _calculate_status(self, product: Product) -> str:
        """
        Calcule le statut d'urgence d'un produit
        """
        stockout_date = await self.forecast_service.calculate_stockout_date(product.id)
        
        if stockout_date is None:
            return "UNKNOWN"
        
        days_until = (stockout_date - date.today()).days
        
        if days_until < 7:
            return "URGENT"
        elif days_until < 30:
            return "WARNING"
        else:
            return "HEALTHY"
```

---

## 5. Pipeline Data Science

### 5.1 Architecture du Pipeline

```
┌─────────────────────────────────────────────────────────┐
│              DAILY_SALES_LOGS (Raw Data)                │
│  Date   │ Product │ Units Sold │ End Stock              │
│  2025-01│  RB-001 │     5      │    20                  │
│  2025-02│  RB-001 │     0      │     0  ← RUPTURE       │
│  2025-03│  RB-001 │     0      │     0  ← RUPTURE       │
│  2025-04│  RB-001 │     8      │    15                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌──────────────────────────────────┐
         │  ALGORITHME 1: Out-of-Stock      │
         │  Correction                      │
         │                                  │
         │  Jours 2025-02, 2025-03:        │
         │  theoretical_units_sold = 5     │
         │  (moyenne 14j avant)             │
         └──────────────────────────────────┘
                          │
                          ▼
         ┌──────────────────────────────────┐
         │  ALGORITHME 2: Outlier Detection │
         │  (IQR Method)                    │
         │                                  │
         │  Si ventes > Q3 + 1.5*IQR:      │
         │  Remplacer par médiane 30j       │
         └──────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│            CLEANED_DEMAND (Cleaned Data)                │
│  Date   │ Product │ Theoretical Sold │ Is Outlier      │
│  2025-01│  RB-001 │      5.0         │   False         │
│  2025-02│  RB-001 │      5.0         │   False ← Corrigé│
│  2025-03│  RB-001 │      5.0         │   False ← Corrigé│
│  2025-04│  RB-001 │      8.0         │   False         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌──────────────────────────────────┐
         │  ALGORITHME 3: Run Rate          │
         │  Calculator                      │
         │                                  │
         │  Run Rate = Moyenne des 30       │
         │  derniers jours de               │
         │  theoretical_units_sold          │
         └──────────────────────────────────┘
                          │
                          ▼
         ┌──────────────────────────────────┐
         │  ALGORITHME 4: Stockout          │
         │  Predictor                       │
         │                                  │
         │  Date Rupture = Aujourd'hui +    │
         │  (Stock / Run Rate)              │
         │                                  │
         │  Qté à Commander = ...           │
         └──────────────────────────────────┘
```

### 5.2 Implémentation Algorithmes

#### Algorithme 1 : Out-of-Stock Correction

```python
# backend/src/modules/forecasting/algorithms/out_of_stock_correction.py
import pandas as pd
from datetime import timedelta

def correct_out_of_stock(df: pd.DataFrame, window_days: int = 14) -> pd.DataFrame:
    """
    Corrige les jours de rupture de stock en injectant une vente théorique.
    
    Args:
        df: DataFrame avec colonnes [product_id, date, units_sold, end_of_day_stock]
        window_days: Nombre de jours pour la moyenne mobile (défaut 14)
    
    Returns:
        DataFrame avec colonne ajoutée [theoretical_units_sold]
    """
    df = df.sort_values(['product_id', 'date']).reset_index(drop=True)
    df['theoretical_units_sold'] = df['units_sold'].astype(float)
    
    for product_id in df['product_id'].unique():
        product_mask = df['product_id'] == product_id
        product_df = df[product_mask].copy()
        
        # Détecter les ruptures
        stockout_indices = product_df[product_df['end_of_day_stock'] == 0].index
        
        for idx in stockout_indices:
            # Fenêtre de 14 jours AVANT la rupture
            start_idx = max(0, idx - window_days)
            window_df = product_df.loc[start_idx:idx-1]
            
            # Moyenne des ventes (exclure les ruptures dans la fenêtre)
            window_df = window_df[window_df['end_of_day_stock'] > 0]
            
            if len(window_df) > 0:
                avg_sales = window_df['units_sold'].mean()
                df.loc[idx, 'theoretical_units_sold'] = avg_sales
            else:
                # Si pas de données dans la fenêtre, utiliser moyenne globale
                global_avg = product_df[product_df['end_of_day_stock'] > 0]['units_sold'].mean()
                df.loc[idx, 'theoretical_units_sold'] = global_avg if not pd.isna(global_avg) else 0
    
    return df
```

**Tests Unitaires :**
```python
# backend/src/modules/forecasting/tests/test_out_of_stock_correction.py
import pytest
import pandas as pd
from datetime import date, timedelta
from ..algorithms.out_of_stock_correction import correct_out_of_stock

def test_simple_stockout_correction():
    """Test correction d'une rupture simple"""
    df = pd.DataFrame({
        'product_id': ['P1'] * 20,
        'date': [date.today() - timedelta(days=i) for i in range(19, -1, -1)],
        'units_sold': [5] * 10 + [0] * 3 + [5] * 7,  # 3 jours de rupture
        'end_of_day_stock': [20] * 10 + [0] * 3 + [15] * 7
    })
    
    result = correct_out_of_stock(df)
    
    # Jours 10, 11, 12 (rupture) doivent avoir theoretical_units_sold ≈ 5
    assert result.loc[10, 'theoretical_units_sold'] == pytest.approx(5.0, abs=0.1)
    assert result.loc[11, 'theoretical_units_sold'] == pytest.approx(5.0, abs=0.1)
    assert result.loc[12, 'theoretical_units_sold'] == pytest.approx(5.0, abs=0.1)

def test_no_stockout():
    """Test que l'algorithme ne modifie pas les données sans rupture"""
    df = pd.DataFrame({
        'product_id': ['P1'] * 10,
        'date': [date.today() - timedelta(days=i) for i in range(9, -1, -1)],
        'units_sold': [5, 6, 4, 5, 7, 5, 6, 5, 4, 5],
        'end_of_day_stock': [20] * 10
    })
    
    result = correct_out_of_stock(df)
    
    # theoretical_units_sold doit être identique à units_sold
    pd.testing.assert_series_equal(
        result['theoretical_units_sold'],
        result['units_sold'].astype(float),
        check_names=False
    )
```

#### Algorithme 2 : Outlier Detection

```python
# backend/src/modules/forecasting/algorithms/outlier_detection.py
import pandas as pd
import numpy as np

def detect_and_smooth_outliers(df: pd.DataFrame, iqr_multiplier: float = 1.5) -> pd.DataFrame:
    """
    Détecte et lisse les outliers via méthode IQR.
    
    Args:
        df: DataFrame avec colonne [theoretical_units_sold]
        iqr_multiplier: Multiplicateur IQR (défaut 1.5 = outliers modérés)
    
    Returns:
        DataFrame avec colonne [is_outlier] et theoretical_units_sold lissé
    """
    df['is_outlier'] = False
    
    for product_id in df['product_id'].unique():
        product_mask = df['product_id'] == product_id
        product_df = df[product_mask].copy()
        
        # Calcul IQR
        Q1 = product_df['theoretical_units_sold'].quantile(0.25)
        Q3 = product_df['theoretical_units_sold'].quantile(0.75)
        IQR = Q3 - Q1
        
        # Seuils
        lower_bound = Q1 - iqr_multiplier * IQR
        upper_bound = Q3 + iqr_multiplier * IQR
        
        # Détecter outliers
        outlier_mask = (product_df['theoretical_units_sold'] < lower_bound) | \
                       (product_df['theoretical_units_sold'] > upper_bound)
        
        outlier_indices = product_df[outlier_mask].index
        
        for idx in outlier_indices:
            # Remplacer par médiane fenêtre ±15 jours
            start_idx = max(0, idx - 15)
            end_idx = min(len(product_df) - 1, idx + 15)
            window_df = product_df.loc[start_idx:end_idx]
            
            # Exclure l'outlier lui-même du calcul
            window_df = window_df[window_df.index != idx]
            
            median_sales = window_df['theoretical_units_sold'].median()
            
            df.loc[idx, 'theoretical_units_sold'] = median_sales
            df.loc[idx, 'is_outlier'] = True
    
    return df
```

---

## 6. Architecture Frontend

### 6.1 Structure Next.js 14 (App Router)

```
frontend/
├── src/
│   ├── app/                     # Pages (App Router)
│   │   ├── layout.tsx           # Layout global
│   │   ├── page.tsx             # Homepage (redirect vers /dashboard)
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── dashboard/
│   │       ├── layout.tsx       # Layout dashboard (sidebar, header)
│   │       ├── page.tsx         # Dashboard principal
│   │       └── products/
│   │           └── [id]/
│   │               └── page.tsx  # Détail produit
│   │
│   ├── components/              # Composants réutilisables
│   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── table.tsx
│   │   │   ├── badge.tsx
│   │   │   └── ...
│   │   ├── layouts/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── DashboardLayout.tsx
│   │   └── common/
│   │       ├── Logo.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorBoundary.tsx
│   │
│   ├── modules/                 # Composants métier
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── useAuth.ts
│   │   ├── dashboard/
│   │   │   ├── KPICards.tsx
│   │   │   ├── ProductsTable.tsx
│   │   │   └── useDashboard.ts
│   │   └── products/
│   │       ├── ProductRow.tsx
│   │       ├── EditLeadTimeModal.tsx
│   │       └── useProducts.ts
│   │
│   ├── graphql/                 # GraphQL queries/mutations
│   │   ├── client.ts            # Apollo Client setup
│   │   ├── queries/
│   │   │   ├── getProducts.ts
│   │   │   └── getKPIs.ts
│   │   └── mutations/
│   │       ├── login.ts
│   │       └── updateProduct.ts
│   │
│   ├── lib/                     # Utilitaires
│   │   ├── utils.ts
│   │   └── formatters.ts        # Date, currency formatters
│   │
│   └── styles/
│       └── globals.css          # Tailwind imports
│
├── public/
│   └── logo.svg                 # Logo Michi
│
├── .env.local
├── next.config.js
├── tailwind.config.ts
└── package.json
```

### 6.2 Exemple : Dashboard Page

```typescript
// frontend/src/app/dashboard/page.tsx
import { Suspense } from 'react';
import { getClient } from '@/graphql/client';
import { GET_DASHBOARD_DATA } from '@/graphql/queries/getDashboardData';
import KPICards from '@/modules/dashboard/KPICards';
import ProductsTable from '@/modules/dashboard/ProductsTable';
import LoadingSpinner from '@/components/common/LoadingSpinner';

export default async function DashboardPage() {
  const client = getClient();
  
  const { data, error } = await client.query({
    query: GET_DASHBOARD_DATA,
  });
  
  if (error) {
    return <ErrorPage error={error} />;
  }
  
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-semibold text-gray-900">
        📊 Dashboard
      </h1>
      
      <KPICards kpis={data.dashboardKPIs} />
      
      <Suspense fallback={<LoadingSpinner />}>
        <ProductsTable products={data.products} />
      </Suspense>
    </div>
  );
}
```

### 6.3 Exemple : ProductsTable Component

```typescript
// frontend/src/modules/dashboard/ProductsTable.tsx
'use client';

import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Product } from '@/types/product';
import { formatDate } from '@/lib/formatters';

interface ProductsTableProps {
  products: Product[];
}

export default function ProductsTable({ products }: ProductsTableProps) {
  const [filter, setFilter] = useState<'all' | 'urgent' | 'warning'>('all');
  
  const filteredProducts = products.filter(p => {
    if (filter === 'urgent') return p.status === 'URGENT';
    if (filter === 'warning') return p.status === 'WARNING';
    return true;
  });
  
  return (
    <div className="space-y-4">
      {/* Filtres */}
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg ${
            filter === 'all' ? 'bg-purple-500 text-white' : 'bg-gray-100'
          }`}
        >
          🟢 Tous ({products.length})
        </button>
        <button
          onClick={() => setFilter('urgent')}
          className={`px-4 py-2 rounded-lg ${
            filter === 'urgent' ? 'bg-red-500 text-white' : 'bg-gray-100'
          }`}
        >
          🔴 Urgent ({products.filter(p => p.status === 'URGENT').length})
        </button>
        <button
          onClick={() => setFilter('warning')}
          className={`px-4 py-2 rounded-lg ${
            filter === 'warning' ? 'bg-yellow-500 text-white' : 'bg-gray-100'
          }`}
        >
          🟡 À surveiller ({products.filter(p => p.status === 'WARNING').length})
        </button>
      </div>
      
      {/* Tableau */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>SKU</TableHead>
            <TableHead>Produit</TableHead>
            <TableHead>Stock</TableHead>
            <TableHead>Date Rupture</TableHead>
            <TableHead>Qté à Commander</TableHead>
            <TableHead>Statut</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredProducts.map(product => (
            <TableRow key={product.id}>
              <TableCell className="font-mono text-sm">
                {product.sku}
              </TableCell>
              <TableCell className="font-medium">
                {product.title}
              </TableCell>
              <TableCell>
                {product.currentInventory} unités
              </TableCell>
              <TableCell>
                {product.stockoutDate 
                  ? formatDate(product.stockoutDate)
                  : 'N/A'
                }
              </TableCell>
              <TableCell>
                {product.recommendedOrderQty > 0
                  ? `${product.recommendedOrderQty} unités`
                  : '-'
                }
              </TableCell>
              <TableCell>
                <Badge variant={getStatusVariant(product.status)}>
                  {getStatusIcon(product.status)} {product.status}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function getStatusVariant(status: string) {
  switch (status) {
    case 'URGENT': return 'destructive';
    case 'WARNING': return 'warning';
    case 'HEALTHY': return 'success';
    default: return 'secondary';
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'URGENT': return '🔴';
    case 'WARNING': return '🟡';
    case 'HEALTHY': return '🟢';
    default: return '⚪';
  }
}
```

---

## 7. Sécurité & Performance

### 7.1 Sécurité

**JWT Authentication :**
```python
# backend/src/core/security.py
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key-here"  # À stocker dans .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**CORS Configuration :**
```python
# backend/src/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://michi.vercel.app"],  # Production
    allow_credentials=True,
    allow_methods=["POST"],  # GraphQL uniquement
    allow_headers=["Authorization", "Content-Type"],
)
```

### 7.2 Performance

**Database Query Optimization :**
- Utiliser `select_in_load` pour éviter N+1 queries
- Index sur toutes les FK et colonnes de tri
- Async queries partout (SQLAlchemy 2.0 Async)

**Caching Strategy :**
```python
# Redis cache pour run_rate (calculé 1x/jour)
from redis import asyncio as aioredis

cache = aioredis.from_url("redis://localhost")

async def get_run_rate(product_id: str) -> float:
    # Check cache
    cached = await cache.get(f"run_rate:{product_id}")
    if cached:
        return float(cached)
    
    # Calcul depuis DB
    run_rate = await calculate_run_rate_from_db(product_id)
    
    # Cache 24h
    await cache.setex(f"run_rate:{product_id}", 86400, run_rate)
    
    return run_rate
```

**GraphQL DataLoader :**
```python
# Batch loading pour éviter N+1
from strawberry.dataloader import DataLoader

async def load_products(keys: List[str]) -> List[Product]:
    """Load multiple products in 1 query"""
    query = select(Product).where(Product.id.in_(keys))
    result = await db.execute(query)
    products = {p.id: p for p in result.scalars().all()}
    return [products.get(key) for key in keys]

product_loader = DataLoader(load_fn=load_products)
```

---

## 8. Déploiement & Infrastructure

### 8.1 Stack de Déploiement

```
┌────────────────────────────────────────────┐
│          VERCEL (Frontend)                 │
│  Next.js 14 SSR + Edge Network            │
│  CDN global, auto-scaling                  │
└──────────────┬─────────────────────────────┘
               │
               │ HTTPS
               ▼
┌────────────────────────────────────────────┐
│         RAILWAY (Backend)                  │
│  FastAPI + GraphQL + Worker                │
│  Auto-scaling, PostgreSQL intégré          │
└────────────────────────────────────────────┘
```

### 8.2 Variables d'Environnement

**Backend (.env) :**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/michi

# JWT
SECRET_KEY=super-secret-key-change-in-prod
ACCESS_TOKEN_EXPIRE_HOURS=24

# Redis (optionnel MVP)
REDIS_URL=redis://localhost:6379

# Sentry (monitoring)
SENTRY_DSN=https://xxx@sentry.io/xxx
```

**Frontend (.env.local) :**
```bash
# API GraphQL
NEXT_PUBLIC_GRAPHQL_URL=https://api.michi.app/graphql

# Analytics (optionnel)
NEXT_PUBLIC_VERCEL_ANALYTICS_ID=xxx
```

### 8.3 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest backend/tests

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test

  deploy-frontend:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: vercel/actions@v1
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}

  deploy-backend:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: railwayapp/actions@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
```

---

## 9. Testing Strategy

### 9.1 Pyramide de Tests

```
           ┌──────────┐
           │   E2E    │  10 tests critiques (Playwright)
           │  Tests   │
           └──────────┘
         ┌──────────────┐
         │ Integration  │  50 tests (GraphQL resolvers)
         │    Tests     │
         └──────────────┘
       ┌──────────────────┐
       │   Unit Tests     │  200+ tests (algorithmes, services)
       │                  │
       └──────────────────┘
```

### 9.2 Exemples de Tests

**Test Unitaire (Algorithme) :**
```python
# backend/src/modules/forecasting/tests/test_stockout_predictor.py
import pytest
from datetime import date, timedelta
from ..algorithms.stockout_predictor import calculate_stockout_date

def test_stockout_prediction_simple():
    """Test calcul date de rupture simple"""
    stock = 30
    run_rate = 2.5  # unités/jour
    
    result = calculate_stockout_date(stock, run_rate)
    
    expected = date.today() + timedelta(days=12)  # 30 / 2.5 = 12 jours
    assert result == expected
```

**Test Integration (GraphQL) :**
```python
# backend/tests/test_graphql_products.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_products_query(client: AsyncClient, auth_token: str):
    """Test query products avec auth"""
    query = """
        query {
            products(limit: 10) {
                id
                sku
                title
                stockoutDate
            }
        }
    """
    
    response = await client.post(
        "/graphql",
        json={"query": query},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "products" in data["data"]
    assert len(data["data"]["products"]) <= 10
```

**Test E2E (Playwright) :**
```typescript
// frontend/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test('user can login and see dashboard', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('input[name="email"]', 'sophie@test.fr');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  // Redirect vers dashboard
  await expect(page).toHaveURL('/dashboard');
  
  // Vérifier KPI cards
  await expect(page.locator('text=Manque à gagner')).toBeVisible();
  
  // Vérifier tableau produits
  await expect(page.locator('table')).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount.greaterThan(0);
});
```

---

## 10. Décisions Techniques (ADR)

### ADR 001 : Choix de GraphQL vs REST

**Statut :** ✅ Accepté  
**Date :** Mars 2026  
**Décideur :** [Votre Nom]

**Contexte :**
Besoin d'une API flexible pour frontend + future mobile app.

**Décision :**
GraphQL avec Strawberry (Python).

**Rationale :**
- Frontend peut demander exactement les champs nécessaires
- Pas de sur-fetching/under-fetching
- Introspection automatique (documentation API)
- Subscriptions futures pour live updates

**Conséquences :**
- Courbe d'apprentissage pour équipe
- Complexity légèrement plus élevée vs REST
- Besoin de DataLoader pour performance

---

### ADR 002 : SQLAlchemy vs Prisma

**Statut :** ✅ Accepté  
**Date :** Mars 2026

**Contexte :**
Besoin d'un ORM performant avec support async.

**Décision :**
SQLAlchemy 2.0 (Async).

**Rationale :**
- Maturité (15+ ans)
- Support async natif depuis 2.0
- Écosystème Python riche (Alembic migrations)
- Data Science : Pandas intégration facile

**Alternatives Rejetées :**
- Prisma : Pas de support Python officiel
- Django ORM : Trop couplé à Django

---

### ADR 003 : Mock Shopify vs Vraie API MVP

**Statut :** ✅ Accepté  
**Date :** Mars 2026

**Contexte :**
Accès Shopify API nécessite app store review (3-4 semaines).

**Décision :**
Mock Data Generator pour MVP, vraie API post-MVP.

**Rationale :**
- Permet de tester algorithmes immédiatement
- Clients pilotes peuvent upload CSV en attendant
- Accélère le time-to-market

**Migration Plan :**
1. MVP : Mock uniquement
2. Post-MVP : Ajouter Shopify API connector
3. Long-term : Support multi-plateformes (WooCommerce, etc.)

---

**Fin de l'Architecture v2.0**
