# AUDIT TECHNIQUE & SPRINT PLANNING — Michi 道
**Version:** 1.0 | **Date:** Avril 2026 | **Auteurs:** Lead Tech + Scrum Master  
**Sprint ciblé :** Sprint 7 — Architecture, Documentation, Tests & i18n

---

## TABLE DES MATIÈRES

1. [Résumé Exécutif](#1-résumé-exécutif)
2. [Audit Technique — État Actuel](#2-audit-technique--état-actuel)
3. [Dettes Techniques Identifiées](#3-dettes-techniques-identifiées)
4. [Architecture Hexagonale Cible](#4-architecture-hexagonale-cible)
5. [EPIC 1 — Architecture Hexagonale](#5-epic-1--architecture-hexagonale)
6. [EPIC 2 — Documentation Docusaurus + API](#6-epic-2--documentation-docusaurus--api)
7. [EPIC 3 — Tests E2E & Core](#7-epic-3--tests-e2e--core)
8. [EPIC 4 — Internationalisation (i18n)](#8-epic-4--internationalisation-i18n)
9. [Sprint Board — Vue Consolidée](#9-sprint-board--vue-consolidée)
10. [Risques & Dépendances](#10-risques--dépendances)
11. [Définition of Done (DoD)](#11-définition-of-done-dod)

---

## 1. RÉSUMÉ EXÉCUTIF

### Objectif du Sprint 7
Transformer Michi d'un monolithe modulaire bien structuré vers une **architecture hexagonale simple**, dotée d'une **documentation vivante** (Docusaurus + API docs), de **tests solides** (85% coverage) et d'un **support i18n** (FR + EN). Ce sprint est un sprint technique (pas de feature utilisateur) mais il est bloquant pour les sprints 8-10 qui ajouteront la prévision avancée et les connecteurs.

### Métriques cibles
| KPI | Actuel | Cible Sprint 7 |
|-----|--------|----------------|
| Coverage backend | ~30% (6 modules sur 7 testés partiellement) | **85%** |
| Coverage frontend | ~2% (1 seul test E2E) | **60%** |
| Resolvers GraphQL avec logique DB directe | **12 resolvers** | **0** |
| Endpoints sans docs formelles | 100% | **0%** |
| Support i18n | ❌ FR hardcodé | ✅ FR + EN |
| Documentation structurée | ❌ Markdown brut | ✅ Docusaurus |

### Vélocité estimée
- **Total Story Points :** 89 points
- **Durée recommandée :** 2 sprints de 2 semaines (Sprint 7A + 7B)
- **Prérequis :** Aucun — refactoring pur, aucune migration DB nécessaire

---

## 2. AUDIT TECHNIQUE — ÉTAT ACTUEL

### 2.1 Architecture Backend

#### Ce qui existe et fonctionne bien ✅

| Composant | Fichier | Qualité |
|-----------|---------|---------|
| Configuration centralisée | `core/config.py` | ✅ Pydantic Settings, bien structuré |
| Gestion DB async | `core/database.py` + `database_utils.py` | ✅ SQLAlchemy 2.0 + SerializedAsyncSession |
| Exceptions structurées | `core/exceptions.py` | ✅ MichiException + ErrorCode |
| Sécurité JWT | `core/security.py` | ✅ Bcrypt 12 rounds, JWT 24h |
| Auth middleware | `core/middleware/auth.py` | ✅ Extraction JWT propre |
| Module Forecasting | `modules/forecasting/algorithms/` | ✅ 6 algorithmes vectorisés + 5 tests |
| Module Billing | `modules/billing/service.py` | ✅ MOCK/STRIPE switchable |

#### Violations architecturales identifiées ❌

**Problème critique #1 — Fat Resolver (schema.py : 760 lignes)**
```
❌ ACTUEL (schema.py, ligne 264-300) :
  - create_organization() : requêtes SQLAlchemy directes dans la mutation
  - select(Organization), select(OrganizationMember)... dans le resolver
  - Logique métier (slug generation, role assignment) dans la mutation

✅ CIBLE hexagonale :
  - Resolver → appelle OrgService.create_organization()
  - OrgService → appelle OrgRepository.save()
  - OrgRepository → SQLAlchemy (isolé en infrastructure)
```

**Problème critique #2 — Couplage Service ↔ Infrastructure**
```
❌ ACTUEL (schema.py, lignes 41, 214) :
  - AuthService reçoit billing_service en constructeur
  - Import direct de models SQLAlchemy dans les resolvers :
    "from src.modules.auth.models import Organization" (ligne 258)
  - 12 resolvers sur 15 font des select() directement

✅ CIBLE :
  - Services ne connaissent pas les modèles SQLAlchemy
  - Services reçoivent des Repository Protocols (interfaces)
  - Billing injecté via Protocol, pas directement
```

**Problème critique #3 — Logique DB dans les Mutations GraphQL**

Mutations qui font du SQL directement (à refactorer) :
- `create_organization` (lignes 258-309) — 50 lignes de SQL dans le resolver
- `switch_organization` (lignes 344-395) — logique token + DB mélangée
- `toggle_source` (lignes 559-609) — select + delete dans le resolver
- `invite_member` (lignes 611-639) — construction ORM inline
- `update_member_permissions` (lignes 641-680) — parse JSON + DB
- `sources` query (lignes 75-98) — select(Store) direct
- `organization_members` (lignes 100-145) — select + selectinload direct
- `pending_invitations` (lignes 147-178) — orchestration directe
- `currentOrganization` (lignes 181-204) — select direct

**Problème critique #4 — Absence de Repository Pattern**

Aucun fichier `repository.py` n'existe dans aucun module.
La persistence est faite inline dans les services ET les resolvers.

**Problème #5 — Google OAuth synchrone (requests bloquant)**
```
❌ ACTUEL (schema.py, ligne 469) :
  resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token=...")
  # requests synchrone dans un contexte async — bloque l'event loop

✅ CIBLE :
  async with httpx.AsyncClient() as client:
      resp = await client.get(...)
```

### 2.2 Architecture Frontend

#### Ce qui existe et fonctionne bien ✅

| Composant | Qualité |
|-----------|---------|
| Apollo Client avec auth link + error link | ✅ Bien configuré |
| Organisation par features (`modules/`, `components/`) | ✅ Bonne séparation |
| React Hook Form + Zod (validation) | ✅ Type-safe |
| Optimistic UI prêt (Apollo cache policies) | ✅ |
| Security headers (next.config.js) | ✅ |

#### Problèmes Frontend identifiés ❌

**Frontend #1 — lang="fr" hardcodé**
```
❌ ACTUEL (app/layout.tsx) :
  <html lang="fr">
  # Aucun fichier de traduction, textes hardcodés en FR partout

✅ CIBLE :
  next-intl avec [locale] routing
  /fr/... et /en/... 
  Messages dans /messages/fr.json + /messages/en.json
```

**Frontend #2 — Absence totale de tests unitaires**
```
❌ ACTUEL :
  - 1 seul fichier Playwright (e2e/sprint1_sync_products.spec.ts)
  - 0 test Vitest dans src/
  - 0 test sur les hooks Apollo (useQuery, useMutation)

✅ CIBLE :
  - 15+ tests E2E Playwright (auth, dashboard, inventory, forecasting)
  - Tests unitaires sur les hooks critiques
  - Tests composants (ProductTable, SalesChart)
```

**Frontend #3 — StoreContext monolithique**
```
❌ ACTUEL (context/StoreContext.tsx) :
  État global non typé, tout dans un seul Context
  
✅ CIBLE :
  Découpage en domaines (AuthContext, OrgContext, UIContext)
```

### 2.3 Tests Existants

#### Backend — Tests actuels
| Fichier | Type | Couverture estimée |
|---------|------|-------------------|
| `modules/auth/tests/test_auth_service.py` | Unit | Login, Register |
| `modules/forecasting/tests/test_predictions.py` | Unit | Algorithme prédiction |
| `modules/forecasting/tests/test_mape.py` | Unit | Métrique MAPE |
| `modules/forecasting/tests/test_outlier_detection.py` | Unit | IQR outliers |
| `modules/forecasting/tests/test_run_rate.py` | Unit | Run Rate 30j |
| `modules/shopify/tests/test_mock_generator.py` | Unit | Mock data gen |
| `modules/shopify/tests/test_validation.py` | Unit | Schéma validation |
| `tests/test_billing_integration.py` | Integration | Stripe MOCK |
| `tests/test_graphql_integration.py` | Integration | Résolveurs principaux |
| `tests/test_inventory_omnichannel.py` | Integration | Sync multi-canal |
| `tests/test_ingestion_woocommerce.py` | Integration | Connecteur WC |

**Gaps critiques :**
- ❌ Aucun test pour `modules/decisions/`
- ❌ Aucun test e2e auth flow (login → onboarding → dashboard)
- ❌ Aucun test permission RBAC
- ❌ Aucun test pour les resolvers refactorisés

#### Frontend — Tests actuels
| Fichier | Type | Couverture |
|---------|------|-----------|
| `e2e/sprint1_sync_products.spec.ts` | E2E Playwright | 1 flux sync |

**Gaps critiques :**
- ❌ 0 test sur auth (login, register, Google OAuth)
- ❌ 0 test sur org switching
- ❌ 0 test sur le dashboard et les charts
- ❌ 0 test sur le forecasting UI
- ❌ 0 test composant (vitest)

### 2.4 Documentation

#### État actuel
| Fichier | Contenu | Format |
|---------|---------|--------|
| `docs/architecture.md` | Architecture globale | Markdown statique |
| `docs/prd.md` | Product Requirements Document | Markdown statique |
| `docs/tracker.md` | Suivi des sprints | Markdown statique |
| `docs/claude.md` | Instructions Claude Code | Markdown statique |
| `docs/quickstart.md` | Démarrage rapide | Markdown statique |
| `docs/project_summary.md` | Résumé projet | Markdown statique |

**Gaps :**
- ❌ Pas de site de documentation interactif
- ❌ Pas de documentation API (GraphQL schema autodoc)
- ❌ Pas de documentation REST (billing_router, shopify_auth_router)
- ❌ Les docs sont uniquement accessibles en local via un éditeur markdown

---

## 3. DETTES TECHNIQUES IDENTIFIÉES

### Tableau de priorité (Impact × Effort × Risque)

| # | Dette | Impact | Effort | Risque si non corrigé | Priorité |
|---|-------|--------|--------|----------------------|----------|
| DT-01 | SQL direct dans resolvers GraphQL | CRITIQUE | M | Regression lors de tout refactoring | 🔴 P0 |
| DT-02 | Google OAuth bloquant (requests sync) | HAUT | XS | Latence, blocage event loop FastAPI | 🔴 P0 |
| DT-03 | Absence couche Repository | HAUT | L | Impossible de changer de DB sans tout réécrire | 🟡 P1 |
| DT-04 | Tests coverage < 30% | HAUT | L | Régressions invisibles en production | 🔴 P0 |
| DT-05 | i18n absent (textes hardcodés FR) | MOYEN | M | Impossible d'internationaliser sans refactor massif | 🟡 P1 |
| DT-06 | Documentation uniquement en Markdown | MOYEN | M | Onboarding développeurs lent | 🟡 P1 |
| DT-07 | StoreContext monolithique | FAIBLE | S | Re-renders globaux inutiles | 🟢 P2 |
| DT-08 | Resolvers trop longs (760 lignes schema.py) | MOYEN | M | Maintenabilité dégradée | 🟡 P1 |

---

## 4. ARCHITECTURE HEXAGONALE CIBLE

### Principe : Ports & Adapters — version simple

```
┌─────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Entities   │  │  Value Obj.  │  │   Domain Events      │  │
│  │ (User, Org,  │  │ (Email, JWT) │  │ (UserCreated, etc.)  │  │
│  │  Product...) │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              PORT INTERFACES (Protocols)                 │   │
│  │  IUserRepository, IProductRepository, IEmailService...  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    USE CASES / SERVICES                  │   │
│  │  AuthService, OrgService, InventoryService,              │   │
│  │  ForecastingService, BillingService...                   │   │
│  │  (Reçoivent des Ports, ne connaissent pas SQLAlchemy)    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐   │
│  │   SQLAlchemy     │  │   Email (SMTP)   │  │   Stripe    │   │
│  │  Repositories    │  │    Adapter       │  │   Adapter   │   │
│  │ (impl. des Port) │  │                  │  │             │   │
│  └──────────────────┘  └──────────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────────────────────────────────────────────┐
│                      ADAPTERS LAYER                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐   │
│  │  GraphQL Resolvers│  │   REST Routes    │  │  CLI Tasks  │   │
│  │  (Thin — appels  │  │  (Shopify OAuth  │  │  (Alembic)  │   │
│  │   services seul) │  │  Billing Routes) │  │             │   │
│  └──────────────────┘  └──────────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Structure des dossiers cible

```
backend/src/
├── core/
│   ├── config.py                    # ✅ inchangé
│   ├── database.py                  # ✅ inchangé
│   ├── database_utils.py            # ✅ inchangé
│   ├── exceptions.py                # ✅ inchangé
│   ├── security.py                  # ✅ inchangé
│   ├── middleware/auth.py           # ✅ inchangé
│   └── graphql/
│       ├── context.py               # ✅ inchangé
│       ├── extensions.py            # ✅ inchangé
│       ├── schema.py                # 🔄 MINCE — délègue aux resolvers de modules
│       └── types.py                 # ✅ inchangé
│
└── modules/
    └── auth/                        # Exemple : module refactorisé
        ├── domain/
        │   ├── entities.py          # 🆕 User, Organization (dataclasses pures)
        │   ├── value_objects.py     # 🆕 Email, HashedPassword
        │   └── ports.py             # 🆕 IUserRepository, IOrgRepository (Protocols)
        ├── application/
        │   └── service.py           # 🔄 AuthService (reçoit IUserRepository)
        ├── infrastructure/
        │   └── repository.py        # 🆕 SQLAlchemyUserRepository (impl. du Port)
        └── adapters/
            └── resolvers.py         # 🔄 Resolvers MINCES (appels service seulement)
```

### Règle d'or de la migration

> Un resolver GraphQL ne doit JAMAIS importer SQLAlchemy, select(), ou un Model.
> Il ne fait qu'appeler `service.method(args)` et mapper le résultat en type GraphQL.

---

## 5. EPIC 1 — ARCHITECTURE HEXAGONALE

**Epic Goal :** Refactorer le backend pour isoler la logique métier de l'infrastructure, sans changer aucun comportement observable par l'utilisateur.  
**Durée estimée :** 5-6 jours dev  
**Total SP :** 34 points

---

### US-HEXA-01 — Couche Domain : Entités & Ports Auth
**En tant que** Lead Tech,  
**Je veux** isoler les entités métier Auth (User, Organization) dans un module `domain/` avec des interfaces Repository (Protocols),  
**Afin que** la logique métier ne dépende plus de SQLAlchemy.

**Story Points :** 5

**Contexte technique :**
- Fichier source : `backend/src/modules/auth/models.py` (SQLAlchemy ORM models)
- Fichier cible : `backend/src/modules/auth/domain/entities.py` + `domain/ports.py`
- Les entités domain sont des dataclasses Python pures (pas de SQLAlchemy)
- Les Ports sont des `typing.Protocol` asynchrones

**Critères d'Acceptation :**
- [ ] `auth/domain/entities.py` contient `UserEntity` et `OrgEntity` (dataclasses pures)
- [ ] `auth/domain/ports.py` contient `IUserRepository(Protocol)` avec : `get_by_id`, `get_by_email`, `save`, `list_by_org`
- [ ] `auth/domain/ports.py` contient `IOrgRepository(Protocol)` avec : `get_by_id`, `save`, `list_by_user`
- [ ] Les entités ne font aucun import de SQLAlchemy ou FastAPI
- [ ] Tests unitaires sur les entités : validation email, hash password
- [ ] `mypy --strict` passe sur le module domain/

**Tâches techniques :**
1. Créer `auth/domain/entities.py` avec UserEntity, OrgEntity, OrgMemberEntity
2. Créer `auth/domain/ports.py` avec IUserRepository, IOrgRepository, IInvitationRepository protocols
3. Créer `auth/domain/value_objects.py` avec Email (validated), HashedPassword
4. Écrire tests `auth/tests/test_domain_entities.py`

---

### US-HEXA-02 — Couche Infrastructure : Repository SQLAlchemy Auth
**En tant que** Lead Tech,  
**Je veux** créer une implémentation `SQLAlchemyUserRepository` qui implémente `IUserRepository`,  
**Afin que** tout accès DB Auth soit centralisé dans un seul fichier infrastructure.

**Story Points :** 5

**Contexte technique :**
- La logique SQL actuellement dispersée dans `schema.py` (resolvers) et `auth/service.py` doit migrer ici
- La session SQLAlchemy est injectée dans le constructeur du repository

**Critères d'Acceptation :**
- [ ] `auth/infrastructure/repository.py` contient `SQLAlchemyUserRepository(IUserRepository)`
- [ ] `SQLAlchemyUserRepository` reçoit `AsyncSession` en constructeur
- [ ] Toutes les opérations DB Auth passent par ce repository (aucun `select()` dans service ou resolver)
- [ ] `auth/infrastructure/org_repository.py` contient `SQLAlchemyOrgRepository`
- [ ] Tests d'intégration : `test_user_repository.py` avec base SQLite in-memory
- [ ] Résolution du bug Google OAuth sync → migration vers `httpx.AsyncClient`

**Tâches techniques :**
1. Créer `auth/infrastructure/user_repository.py` — migrer les select() de service.py + schema.py
2. Créer `auth/infrastructure/org_repository.py` — migrer les queries Organization
3. Créer `auth/infrastructure/invitation_repository.py` — migrer les queries Invitation
4. Remplacer `requests.get()` par `httpx.AsyncClient` dans `googleLogin`
5. Écrire `auth/tests/test_user_repository.py`

---

### US-HEXA-03 — Couche Application : Refactoring AuthService & OrgService
**En tant que** Lead Tech,  
**Je veux** que AuthService et OrgService reçoivent uniquement des interfaces Repository (pas de SQLAlchemy direct),  
**Afin que** les services soient testables sans DB.

**Story Points :** 5

**Contexte technique :**
- `auth/service.py` reçoit actuellement `db: AsyncSession` → doit recevoir `IUserRepository`
- `auth/service.py` reçoit `billing_service: BillingService` → doit recevoir `IBillingService(Protocol)`
- La création d'organisation actuellement dans `schema.py` (300+ lignes) doit migrer dans `OrgService`

**Critères d'Acceptation :**
- [ ] `AuthService.__init__(user_repo: IUserRepository, billing: IBillingService)` — plus de AsyncSession
- [ ] `OrgService.__init__(org_repo: IOrgRepository, user_repo: IUserRepository, billing: IBillingService)`
- [ ] `OrgService.create_organization(user_id, name, plan)` contient la logique de `schema.py:create_organization`
- [ ] `OrgService.switch_organization(user_id, org_id)` contient la logique de `schema.py:switch_organization`
- [ ] Tests unitaires avec mock repositories (sans DB)
- [ ] `IBillingService(Protocol)` défini dans `billing/domain/ports.py`

**Tâches techniques :**
1. Créer `billing/domain/ports.py` avec `IBillingService` Protocol
2. Refactorer `AuthService` pour recevoir les interfaces
3. Créer `OrgService` en extrayant la logique de `schema.py`
4. Écrire `auth/tests/test_auth_service_unit.py` avec mocks
5. Écrire `auth/tests/test_org_service_unit.py` avec mocks

---

### US-HEXA-04 — Resolvers GraphQL minces (Auth + Org)
**En tant que** Lead Tech,  
**Je veux** que les resolvers GraphQL Auth/Org ne fassent qu'appeler les services,  
**Afin que** `schema.py` passe de 760 lignes à < 200 lignes.

**Story Points :** 8

**Contexte technique :**
- `schema.py` actuel : 760 lignes, mélange auth + org + réseau + DB
- Objectif : `schema.py` < 200 lignes, délégue aux modules resolvers
- Les mutations `create_organization`, `switch_organization`, `toggle_source`, `invite_member`, etc. migrent dans leurs modules respectifs

**Critères d'Acceptation :**
- [ ] `auth/adapters/resolvers.py` contient `AuthMutation` et `AuthQuery` Strawberry classes
- [ ] Chaque mutation/query ne dépasse pas 15 lignes (appel service + mapping type)
- [ ] `schema.py` < 200 lignes — uniquement composition Query + Mutation
- [ ] Zéro import de SQLAlchemy dans les resolvers
- [ ] Zéro `select()`, `delete()`, `execute()` dans les resolvers
- [ ] Tous les tests d'intégration GraphQL existants passent toujours

**Mutations à migrer (9 sur 15) :**
1. `create_organization` → `OrgService.create_organization()`
2. `switch_organization` → `OrgService.switch_organization()`
3. `toggle_source` → `InventoryService.toggle_source()`
4. `invite_member` → `InvitationService.create_invitation()`
5. `update_member_permissions` → `OrgService.update_permissions()`
6. `accept_invitation` → `InvitationService.accept()`
7. `delete_invitation` → `InvitationService.delete()`
8. `remove_member` → `OrgService.remove_member()`
9. `update_member_role` → `OrgService.update_role()`

**Queries à migrer (5 sur 8) :**
1. `sources` → `InventoryService.get_stores()`
2. `organization_members` → `OrgService.get_members()`
3. `pending_invitations` → `InvitationService.get_pending()`
4. `currentOrganization` → `OrgService.get_current()`
5. `me` → `AuthService.get_me()`

**Tâches techniques :**
1. Créer `auth/adapters/resolvers.py` avec AuthQuery + AuthMutation
2. Créer `auth/adapters/org_resolvers.py` avec OrgQuery + OrgMutation
3. Refactorer `schema.py` → composition pure
4. Valider que `test_graphql_integration.py` passe toujours
5. Valider que l'app frontend tourne sans régression

---

### US-HEXA-05 — Application de la même structure aux modules Inventory et Forecasting
**En tant que** Lead Tech,  
**Je veux** appliquer la structure hexagonale aux modules Inventory et Forecasting,  
**Afin d'assurer** la cohérence architecturale sur les 2 modules les plus utilisés.

**Story Points :** 8

**Contexte technique :**
- `inventory/resolvers.py` : à auditer pour SQL direct
- `forecasting/resolvers.py` : à auditer
- Priorité sur ces 2 modules car ils contiennent la valeur métier principale

**Critères d'Acceptation :**
- [ ] `inventory/domain/ports.py` avec `IProductRepository`, `IStoreRepository`, `IAlertRepository`
- [ ] `inventory/infrastructure/repository.py` avec implémentations SQLAlchemy
- [ ] `inventory/application/service.py` refactorisé (reçoit IProductRepository)
- [ ] `forecasting/domain/ports.py` avec `IPredictionRepository`
- [ ] `forecasting/infrastructure/repository.py` implémentée
- [ ] Resolvers Inventory et Forecasting minces (< 15 lignes chaque)
- [ ] Tests unitaires services avec mocks

**Tâches techniques :**
1. Audit `inventory/resolvers.py` — identifier le SQL direct
2. Créer les Ports Inventory
3. Créer `inventory/infrastructure/repository.py`
4. Refactorer `InventoryService`
5. Appliquer la même logique sur `forecasting/`
6. Tests unitaires

---

### US-HEXA-06 — Dependency Injection Container (contexte GraphQL)
**En tant que** Lead Tech,  
**Je veux** que le contexte GraphQL construise les services via injection de dépendances propre,  
**Afin d'éviter** la création manuelle de services dans chaque resolver.

**Story Points :** 3

**Contexte technique :**
- Actuellement : `AuthService(info.context.db, billing_service=info.context.billing)` dans chaque resolver
- Cible : `info.context.auth_service`, `info.context.org_service` pré-construits dans `get_context()`

**Critères d'Acceptation :**
- [ ] `GraphQLContext` expose : `auth_service`, `org_service`, `inventory_service`, `forecasting_service`
- [ ] Les services sont construits une fois par requête dans `get_context()`
- [ ] Les resolvers font juste `info.context.auth_service.login(...)` sans instancier de service
- [ ] La session DB est injectée dans les repositories qui sont injectés dans les services

**Tâches techniques :**
1. Modifier `core/graphql/context.py` — ajouter services pré-construits
2. Créer une factory `build_services(db, billing)` dans `core/di.py`
3. Mettre à jour tous les resolvers refactorisés pour utiliser `info.context.X_service`

---

## 6. EPIC 2 — DOCUMENTATION DOCUSAURUS + API

**Epic Goal :** Mettre en place un site de documentation Docusaurus avec la doc technique, les guides et la référence API GraphQL auto-générée.  
**Durée estimée :** 3-4 jours dev  
**Total SP :** 21 points

---

### US-DOC-01 — Setup Docusaurus 3 dans le monorepo
**En tant que** développeur rejoignant le projet,  
**Je veux** accéder à une documentation structurée et navigable sur `http://localhost:3001`,  
**Afin de** comprendre rapidement l'architecture et les APIs sans lire des fichiers Markdown bruts.

**Story Points :** 5

**Contexte technique :**
- Docusaurus 3.x (React-based, MDX support)
- Placé dans `/docs-site/` à la racine du projet (pas dans `/docs/`)
- Les fichiers Markdown existants dans `/docs/*.md` sont migrés

**Critères d'Acceptation :**
- [ ] `docs-site/` créé avec `npx create-docusaurus@latest docs-site classic --typescript`
- [ ] `docs-site/package.json` configuré, `npm run start` lance sur port 3001
- [ ] Navigation structurée en 4 sections : Guide, Architecture, API Reference, Sprints
- [ ] Les 7 fichiers Markdown existants (`docs/*.md`) migrés en MDX dans `docs-site/docs/`
- [ ] Thème personnalisé couleurs Michi (violet `#7C3AED`, fond sombre)
- [ ] Sidebar auto-générée depuis la structure de fichiers
- [ ] `docs-site` ajouté au `.gitignore` pour `node_modules` seulement (le code est versionné)
- [ ] Script npm `"docs": "cd docs-site && npm run start"` dans le root `package.json`

**Tâches techniques :**
1. Initialiser Docusaurus dans `docs-site/`
2. Configurer `docusaurus.config.ts` (titre, thème, navbar, footer)
3. Migrer et adapter les 7 fichiers Markdown existants
4. Créer la structure de navigation (sidebars.ts)
5. Personnaliser le thème CSS (brand colors)
6. Tester le build `npm run build`

---

### US-DOC-02 — Documentation d'architecture avec diagrammes
**En tant que** développeur,  
**Je veux** que la documentation d'architecture inclue des diagrammes clairs (Mermaid),  
**Afin de** visualiser les flux de données et les couches architecturales.

**Story Points :** 3

**Contexte technique :**
- Docusaurus 3 supporte Mermaid nativement avec le plugin `@docusaurus/theme-mermaid`
- Diagrammes à créer : architecture hexagonale, flux auth, flux forecasting pipeline

**Critères d'Acceptation :**
- [ ] `docs-site/docs/architecture/hexagonal.mdx` avec diagramme Mermaid de l'architecture
- [ ] `docs-site/docs/architecture/auth-flow.mdx` avec le flux JWT + Google OAuth
- [ ] `docs-site/docs/architecture/forecasting-pipeline.mdx` avec les 6 étapes algorithme
- [ ] `docs-site/docs/architecture/database-schema.mdx` avec ERD Mermaid (tables principales)
- [ ] Plugin Mermaid activé dans `docusaurus.config.ts`
- [ ] Tous les diagrammes s'affichent correctement dans le browser

**Tâches techniques :**
1. Activer `@docusaurus/theme-mermaid` dans la config
2. Créer les 4 pages de documentation avec diagrammes
3. ERD Mermaid basé sur les 16 migrations Alembic

---

### US-DOC-03 — GraphQL API Reference auto-générée
**En tant que** développeur frontend ou partenaire technique,  
**Je veux** consulter une référence complète de l'API GraphQL générée automatiquement depuis le schéma,  
**Afin de** savoir quelles queries/mutations sont disponibles sans lire le code source.

**Story Points :** 5

**Contexte technique :**
- Strawberry GraphQL expose un schéma introspectable
- Utiliser `graphql-markdown` ou export SDL vers `spectaql` ou `docusaurus-graphql-doc-generator`
- Alternative simple : exporter le schéma SDL + l'intégrer dans Docusaurus avec syntax highlighting

**Critères d'Acceptation :**
- [ ] `backend/scripts/export_schema.py` génère `docs-site/static/schema.graphql`
- [ ] Page Docusaurus `docs-site/docs/api/graphql.mdx` avec la liste de toutes les queries/mutations
- [ ] Chaque query/mutation documentée avec : signature, paramètres, type retour, exemple
- [ ] Les 8 queries documentées : `me`, `sources`, `organizationMembers`, `products`, `predictions`, `getDashboardStats`, `getProductDetail`, `getUnreadAlerts`
- [ ] Les 15+ mutations documentées avec exemples
- [ ] Script `npm run generate:api-docs` dans `docs-site/package.json`
- [ ] La page s'affiche correctement dans Docusaurus

**Tâches techniques :**
1. Créer `backend/scripts/export_schema.py` (introspection Strawberry → SDL file)
2. Choisir et configurer le plugin docusaurus approprié
3. Écrire manuellement les exemples pour les 8 queries principales
4. Écrire manuellement les exemples pour les 15 mutations principales
5. Documenter les 2 routes REST (Shopify OAuth, Billing) en MDX

---

### US-DOC-04 — Guide Développeur & Quickstart
**En tant que** nouveau développeur rejoignant Michi,  
**Je veux** un guide de démarrage complet qui me permet d'avoir l'app qui tourne en < 10 minutes,  
**Afin de** contribuer rapidement sans avoir besoin d'aide d'un autre dev.

**Story Points :** 3

**Contexte technique :**
- Le `docs/quickstart.md` existant est minimal
- Doit couvrir : setup Docker, backend Python, frontend Next.js, variables d'environnement, test login

**Critères d'Acceptation :**
- [ ] `docs-site/docs/guide/quickstart.mdx` avec étapes numérotées et blocs de code copiables
- [ ] Prérequis listés (Python 3.12, Node 18+, Docker Desktop, Git)
- [ ] Section "Backend Setup" : `docker-compose up`, migrations Alembic, `uvicorn` dev server
- [ ] Section "Frontend Setup" : `npm install`, `.env.local`, `npm run dev`
- [ ] Section "Premier Login" : credentials de test, navigation dashboard
- [ ] Section "Architecture Overview" : lien vers les pages architecture
- [ ] Tous les blocs de code testés et valides
- [ ] Temps de setup validé < 10 minutes sur une machine propre

**Tâches techniques :**
1. Rédiger `quickstart.mdx` complet
2. Créer `docs-site/docs/guide/contributing.mdx` (conventions de commit, PR process)
3. Créer `docs-site/docs/guide/environment.mdx` (toutes les env vars documentées)
4. Valider sur machine propre

---

### US-DOC-05 — Documentation des algorithmes de prévision
**En tant que** Data Scientist ou PM,  
**Je veux** que chaque algorithme de forecasting soit documenté avec la formule mathématique et les paramètres,  
**Afin de** comprendre et valider les calculs de prédiction.

**Story Points :** 5

**Contexte technique :**
- 6 algorithmes dans `forecasting/algorithms/` : run_rate, outlier_detection, out_of_stock_correction, seasonality, abc_analysis, predictions
- Docusaurus supporte KaTeX pour les formules mathématiques (plugin `remark-math` + `rehype-katex`)

**Critères d'Acceptation :**
- [ ] Plugin KaTeX activé dans Docusaurus
- [ ] `docs-site/docs/algorithms/run-rate.mdx` — formule Run Rate, paramètre 30j, edge cases
- [ ] `docs-site/docs/algorithms/outlier-detection.mdx` — méthode IQR, formule, visualisation
- [ ] `docs-site/docs/algorithms/out-of-stock-correction.mdx` — correction 14j avg
- [ ] `docs-site/docs/algorithms/abc-analysis.mdx` — classification A/B/C, seuils
- [ ] `docs-site/docs/algorithms/seasonality.mdx` — décomposition saisonnière
- [ ] `docs-site/docs/algorithms/predictions.mdx` — pipeline complet, MAPE cible
- [ ] Chaque page inclut : formule LaTeX, paramètres, exemple d'input/output, métriques de qualité

**Tâches techniques :**
1. Activer `remark-math` + `rehype-katex` dans docusaurus.config.ts
2. Extraire et documenter les formules des 6 fichiers Python
3. Créer les 6 pages MDX avec formules et exemples

---

## 7. EPIC 3 — TESTS E2E & CORE

**Epic Goal :** Atteindre 85% de coverage backend et 60% coverage frontend, couvrir tous les flux critiques avec des tests E2E Playwright robustes.  
**Durée estimée :** 4-5 jours dev  
**Total SP :** 21 points

---

### US-TEST-01 — Tests E2E : Flux d'authentification complet
**En tant que** QA Engineer,  
**Je veux** des tests E2E couvrant tous les cas d'authentification (register, login, Google, logout),  
**Afin de** détecter toute régression sur le flux le plus critique de l'application.

**Story Points :** 5

**Contexte technique :**
- Framework : Playwright 1.41.0 (déjà configuré dans `playwright.config.ts`)
- Base URL : `http://localhost:3000`
- Credentiels de test : à définir dans `.env.test`

**Critères d'Acceptation :**
- [ ] `e2e/auth/register.spec.ts` — register success, email invalide, password trop court, email déjà existant
- [ ] `e2e/auth/login.spec.ts` — login success, mauvais password, user inexistant, remember me
- [ ] `e2e/auth/logout.spec.ts` — logout nettoie le token, redirige vers /login
- [ ] `e2e/auth/onboarding.spec.ts` — après register → onboarding → création org → dashboard
- [ ] `e2e/auth/org-switch.spec.ts` — switch entre 2 orgs, vérifier que le token change
- [ ] Les tests utilisent des fixtures Playwright (page objects pattern)
- [ ] `.env.test` avec `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`, `TEST_API_URL`
- [ ] Les tests passent dans le CI (GitHub Actions ou local)
- [ ] Temps d'exécution < 60 secondes pour les 5 fichiers

**Tâches techniques :**
1. Créer `e2e/fixtures/auth.fixtures.ts` (page objects : LoginPage, RegisterPage)
2. Écrire `e2e/auth/register.spec.ts` (4 cas)
3. Écrire `e2e/auth/login.spec.ts` (4 cas)
4. Écrire `e2e/auth/logout.spec.ts` (2 cas)
5. Écrire `e2e/auth/onboarding.spec.ts` (flux complet)
6. Écrire `e2e/auth/org-switch.spec.ts`
7. Créer `e2e/helpers/db-seed.ts` pour seed la DB de test

---

### US-TEST-02 — Tests E2E : Dashboard & Inventaire
**En tant que** QA Engineer,  
**Je veux** des tests E2E sur le dashboard principal et la gestion de l'inventaire,  
**Afin de** m'assurer que les fonctionnalités coeur (sync, liste produits, alertes) ne régressent pas.

**Story Points :** 5

**Contexte technique :**
- Dépend de `US-TEST-01` (fixtures auth)
- Les tests doivent s'authentifier avant de tester le dashboard

**Critères d'Acceptation :**
- [ ] `e2e/dashboard/stats.spec.ts` — vérifier que les 4 KPI cards s'affichent
- [ ] `e2e/dashboard/product-table.spec.ts` — filtres, tri, pagination, recherche
- [ ] `e2e/dashboard/product-detail.spec.ts` — navigation vers produit, graphique ventes, forecast
- [ ] `e2e/inventory/connect-source.spec.ts` — connecter CSV, Shopify mock, WooCommerce mock
- [ ] `e2e/inventory/sync.spec.ts` — déclencher un sync, vérifier les produits importés
- [ ] `e2e/inventory/alerts.spec.ts` — vérifier que les alertes rupture apparaissent
- [ ] Tous les tests utilisent un état de DB seedé (pas de données hardcodées)
- [ ] Screenshots automatiques en cas d'échec (`trace: 'on-first-retry'`)

**Tâches techniques :**
1. Créer `e2e/fixtures/dashboard.fixtures.ts` avec DashboardPage object
2. Écrire les 6 specs E2E
3. Créer `e2e/helpers/api-mock.ts` pour mocker les appels Shopify/WooCommerce externes
4. Configurer les seeds pour les produits de test

---

### US-TEST-03 — Tests Core Backend : Services & Resolvers refactorisés
**En tant que** Lead Tech,  
**Je veux** que chaque service et repository issu de la migration hexagonale ait des tests unitaires,  
**Afin de** garantir que le refactoring n'a pas cassé de comportements.

**Story Points :** 5

**Contexte technique :**
- Dépend de `US-HEXA-01` à `US-HEXA-05`
- Tests avec repositories mockés (pas de DB) pour les services
- Tests avec SQLite in-memory pour les repositories

**Critères d'Acceptation :**
- [ ] `auth/tests/test_auth_service_unit.py` — login OK, login mauvais password, register duplicate email
- [ ] `auth/tests/test_org_service_unit.py` — create org, switch org, remove member
- [ ] `auth/tests/test_user_repository.py` — CRUD avec SQLite in-memory
- [ ] `inventory/tests/test_inventory_service_unit.py` — toggle source, get products
- [ ] `forecasting/tests/test_forecasting_service_unit.py` — pipeline complet
- [ ] `decisions/tests/test_decisions_service.py` — recommendations (module actuellement sans test)
- [ ] Coverage backend ≥ 85% (`pytest --cov=src --cov-report=html`)
- [ ] Aucun test ne fait appel à une base PostgreSQL réelle (tests unitaires = SQLite ou mock)

**Tâches techniques :**
1. Créer `conftest.py` avec fixture SQLite in-memory pour les tests de repository
2. Créer `conftest.py` avec factories de mock repositories pour les tests de service
3. Écrire les tests pour chaque service (auth, org, inventory, forecasting, decisions)
4. Écrire les tests pour chaque repository
5. Configurer `pytest --cov` avec rapport minimum 85%

---

### US-TEST-04 — Tests Frontend : Composants critiques (Vitest)
**En tant que** développeur frontend,  
**Je veux** des tests unitaires sur les composants et hooks les plus critiques,  
**Afin de** détecter les régressions de rendering sans lancer le serveur.

**Story Points :** 3

**Contexte technique :**
- Vitest 1.2.0 configuré mais 0 test existant
- `@testing-library/react` à installer
- Composants prioritaires : ProductTable, SalesChart, StatsOverview, DashboardHeader

**Critères d'Acceptation :**
- [ ] `@testing-library/react` et `@testing-library/jest-dom` installés
- [ ] `vitest.config.ts` configuré avec jsdom environment
- [ ] `src/components/__tests__/ProductTable.test.tsx` — render avec données mock, filtre, tri
- [ ] `src/components/__tests__/StatsOverview.test.tsx` — affichage des 4 KPIs
- [ ] `src/modules/auth/__tests__/useAuth.test.ts` — hook login, logout
- [ ] `src/graphql/__tests__/client.test.ts` — auth link injecte le token
- [ ] Coverage frontend ≥ 60% (`vitest --coverage`)
- [ ] Tests s'exécutent en < 30 secondes

**Tâches techniques :**
1. Installer `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`
2. Configurer `vitest.config.ts` avec setup file
3. Créer `src/test/setup.ts` (configure jest-dom matchers)
4. Écrire les 4 fichiers de tests composants
5. Écrire les 2 fichiers de tests hooks/client

---

### US-TEST-05 — Pipeline CI : Exécution automatique des tests
**En tant que** DevOps Engineer,  
**Je veux** que les tests backend et frontend s'exécutent automatiquement à chaque PR,  
**Afin de** bloquer les merges qui cassent des tests.

**Story Points :** 3

**Contexte technique :**
- GitHub Actions (`.github/workflows/`)
- Backend : `pytest` avec PostgreSQL de test (service GitHub Actions)
- Frontend : `vitest` + `playwright` en headless

**Critères d'Acceptation :**
- [ ] `.github/workflows/test-backend.yml` — pytest avec PostgreSQL service, coverage report
- [ ] `.github/workflows/test-frontend.yml` — vitest + playwright headless
- [ ] Les workflows se déclenchent sur `push` vers `main` et sur les PRs
- [ ] Les workflows affichent le coverage en commentaire de PR
- [ ] Temps d'exécution CI < 5 minutes
- [ ] Badge de status CI dans le README

**Tâches techniques :**
1. Créer `.github/workflows/test-backend.yml`
2. Créer `.github/workflows/test-frontend.yml`
3. Configurer les secrets GitHub (DATABASE_URL test, etc.)
4. Ajouter le badge status dans `README.md`
5. Tester le workflow sur une PR de test

---

## 8. EPIC 4 — INTERNATIONALISATION (i18n)

**Epic Goal :** Implémenter `next-intl` pour supporter FR et EN, avec routing `/[locale]/...`, sans casser aucune feature existante.  
**Durée estimée :** 3 jours dev  
**Total SP :** 13 points

---

### US-I18N-01 — Setup next-intl avec routing [locale]
**En tant que** développeur frontend,  
**Je veux** configurer `next-intl` avec le routing `[locale]` de Next.js App Router,  
**Afin que** les URLs `/fr/dashboard` et `/en/dashboard` fonctionnent correctement.

**Story Points :** 5

**Contexte technique :**
- Next.js 14 App Router
- `next-intl` v3.x (compatible App Router)
- Routing : `/app/[locale]/layout.tsx`, `/app/[locale]/dashboard/page.tsx`, etc.
- Locales supportées : `fr` (défaut), `en`
- Middleware Next.js pour la détection et redirection de locale

**Critères d'Acceptation :**
- [ ] `next-intl` installé (`npm install next-intl`)
- [ ] `src/middleware.ts` configuré avec `createMiddleware` pour la détection de locale
- [ ] `/app/[locale]/layout.tsx` — root layout avec `<NextIntlClientProvider>`
- [ ] Toutes les routes existantes migrées sous `/app/[locale]/` :
  - `/app/[locale]/page.tsx` (landing)
  - `/app/[locale]/login/page.tsx`
  - `/app/[locale]/register/page.tsx`
  - `/app/[locale]/onboarding/page.tsx`
  - `/app/[locale]/dashboard/page.tsx`
  - `/app/[locale]/dashboard/product/[id]/page.tsx`
  - `/app/[locale]/dashboard/profile/page.tsx`
- [ ] `next.config.js` mis à jour avec le plugin next-intl
- [ ] Redirection automatique `/` → `/fr/` pour les visiteurs sans préférence
- [ ] `lang` attribute dynamique dans le `<html>` tag

**Tâches techniques :**
1. Installer `next-intl` + configurer `middleware.ts`
2. Déplacer toutes les routes dans `/app/[locale]/`
3. Configurer `next.config.js` avec `withNextIntl`
4. Créer `src/i18n.ts` (configuration next-intl)
5. Tester les redirections et le routing

---

### US-I18N-02 — Fichiers de traduction FR & EN + extraction
**En tant que** développeur,  
**Je veux** créer les fichiers de traduction FR et EN et extraire tous les textes hardcodés,  
**Afin que** toutes les chaînes de l'application soient traduisibles.

**Story Points :** 5

**Contexte technique :**
- Fichiers : `messages/fr.json` et `messages/en.json`
- Environ 80-100 chaînes à extraire sur les 8 pages
- Structure par namespace : `auth`, `dashboard`, `inventory`, `forecasting`, `common`, `errors`

**Critères d'Acceptation :**
- [ ] `messages/fr.json` créé avec tous les textes FR de l'application
- [ ] `messages/en.json` créé avec les traductions EN correspondantes
- [ ] Structure JSON organisée par namespaces :
  ```json
  {
    "common": { "save": "Enregistrer", "cancel": "Annuler", ... },
    "auth": { "login": "Se connecter", "email": "Email", ... },
    "dashboard": { "title": "Tableau de bord", ... },
    "inventory": { ... },
    "forecasting": { ... },
    "errors": { "notFound": "Introuvable", ... }
  }
  ```
- [ ] Toutes les pages utilisent `useTranslations()` hook (aucun texte hardcodé)
- [ ] Les messages d'erreur GraphQL (`MichiException`) ont des codes traduits
- [ ] Aucun `console.error` ou `throw Error` avec texte FR hardcodé

**Tâches techniques :**
1. Créer `messages/fr.json` (extraction manuelle des textes des 8 pages + composants)
2. Créer `messages/en.json` (traduction EN)
3. Remplacer les textes hardcodés page par page (landing, login, register, onboarding, dashboard, profile)
4. Remplacer les textes dans les composants (ProductTable, SalesChart, DashboardHeader, etc.)
5. Vérifier l'absence de textes hardcodés avec un grep : `git grep -E '"[A-Za-zÀ-ÿ ]{4,}"' src/`

---

### US-I18N-03 — Sélecteur de langue dans l'UI
**En tant qu'** utilisateur,  
**Je veux** pouvoir changer la langue de l'application depuis la navbar,  
**Afin de** basculer entre français et anglais selon ma préférence.

**Story Points :** 3

**Contexte technique :**
- Composant `LanguageSwitcher` dans la navbar
- Utilise le router Next.js pour changer le locale dans l'URL
- La préférence est persistée dans `localStorage`

**Critères d'Acceptation :**
- [ ] Composant `src/components/LanguageSwitcher.tsx` créé
- [ ] Le sélecteur apparaît dans la Navbar (entre les autres éléments)
- [ ] Clic sur "EN" → redirection vers `/en/[chemin actuel]` sans rechargement complet
- [ ] Clic sur "FR" → redirection vers `/fr/[chemin actuel]`
- [ ] La préférence langue est sauvegardée dans `localStorage`
- [ ] Au prochain chargement, la locale préférée est restaurée
- [ ] Le sélecteur est responsive (icône drapeau sur mobile, texte sur desktop)
- [ ] Les flags FR/EN utilisent des émojis ou des SVG accessibles (aria-label)

**Tâches techniques :**
1. Créer `src/components/LanguageSwitcher.tsx`
2. Intégrer dans `src/components/layout/Navbar.tsx`
3. Implémenter la persistence `localStorage`
4. Tester le switch sur toutes les pages

---

## 9. SPRINT BOARD — VUE CONSOLIDÉE

### Sprint 7A (Semaine 1-2) — Foundation

| US | Titre | SP | Priorité | Dépendances |
|----|-------|----|----------|-------------|
| US-HEXA-01 | Domain : Entités & Ports Auth | 5 | 🔴 P0 | — |
| US-HEXA-02 | Infrastructure : Repository SQLAlchemy Auth | 5 | 🔴 P0 | HEXA-01 |
| US-HEXA-03 | Application : Refactoring AuthService & OrgService | 5 | 🔴 P0 | HEXA-01, HEXA-02 |
| US-HEXA-06 | DI Container (GraphQL Context) | 3 | 🟡 P1 | HEXA-03 |
| US-DOC-01 | Setup Docusaurus 3 | 5 | 🟡 P1 | — |
| US-DOC-02 | Architecture avec diagrammes Mermaid | 3 | 🟡 P1 | DOC-01 |
| **TOTAL 7A** | | **26 SP** | | |

### Sprint 7B (Semaine 3-4) — Delivery

| US | Titre | SP | Priorité | Dépendances |
|----|-------|----|----------|-------------|
| US-HEXA-04 | Resolvers GraphQL minces (Auth + Org) | 8 | 🔴 P0 | HEXA-01→03 |
| US-HEXA-05 | Structure hexagonale Inventory + Forecasting | 8 | 🔴 P0 | HEXA-04 |
| US-DOC-03 | GraphQL API Reference auto-générée | 5 | 🟡 P1 | DOC-01 |
| US-DOC-04 | Guide Développeur & Quickstart | 3 | 🟡 P1 | DOC-01 |
| US-DOC-05 | Documentation algorithmes (LaTeX) | 5 | 🟡 P1 | DOC-01 |
| US-TEST-01 | E2E : Auth flow complet | 5 | 🔴 P0 | — |
| US-TEST-02 | E2E : Dashboard & Inventaire | 5 | 🟡 P1 | TEST-01 |
| US-TEST-03 | Core Backend : Services & Repositories | 5 | 🔴 P0 | HEXA-04, HEXA-05 |
| US-TEST-04 | Frontend : Composants (Vitest) | 3 | 🟡 P1 | — |
| US-TEST-05 | Pipeline CI GitHub Actions | 3 | 🟡 P1 | TEST-01→04 |
| US-I18N-01 | Setup next-intl + routing [locale] | 5 | 🟡 P1 | — |
| US-I18N-02 | Fichiers traduction FR & EN | 5 | 🟡 P1 | I18N-01 |
| US-I18N-03 | Sélecteur de langue UI | 3 | 🟢 P2 | I18N-01, I18N-02 |
| **TOTAL 7B** | | **63 SP** | | |

### Récapitulatif Global

| Epic | US | SP | Durée estimée |
|------|----|----|---------------|
| EPIC 1 — Architecture Hexagonale | 6 US | 34 SP | 5-6 jours |
| EPIC 2 — Documentation Docusaurus | 5 US | 21 SP | 3-4 jours |
| EPIC 3 — Tests E2E & Core | 5 US | 21 SP | 4-5 jours |
| EPIC 4 — i18n | 3 US | 13 SP | 3 jours |
| **TOTAL** | **19 US** | **89 SP** | **~4 semaines** |

---

## 10. RISQUES & DÉPENDANCES

### Risques techniques

| # | Risque | Probabilité | Impact | Mitigation |
|---|--------|-------------|--------|------------|
| R-01 | La migration hexagonale casse des comportements existants | MOYEN | CRITIQUE | Tests d'intégration GraphQL exécutés avant et après chaque US |
| R-02 | next-intl incompatible avec certains composants RSC | FAIBLE | HAUT | Vérifier les composants 'use client' avant migration |
| R-03 | Export schema Strawberry génère un SDL incomplet | FAIBLE | MOYEN | Valider avec `strawberry export-schema` avant de développer la page API docs |
| R-04 | Tests E2E instables (flaky tests) | MOYEN | MOYEN | Utiliser `waitForSelector` + retries Playwright, éviter les `sleep` |
| R-05 | Coverage 85% non atteignable sans refactoring massif | FAIBLE | MOYEN | Prioriser les modules à plus haute valeur (auth, forecasting, inventory) |

### Dépendances critiques

```
US-HEXA-01 ──▶ US-HEXA-02 ──▶ US-HEXA-03 ──▶ US-HEXA-04 ──▶ US-HEXA-05
                                                     │
                                                     ▼
                                              US-TEST-03 (tests des services refactorisés)
                                              
US-DOC-01 ──▶ US-DOC-02, 03, 04, 05 (tous dépendent du setup Docusaurus)

US-TEST-01 ──▶ US-TEST-02 (le dashboard test utilise les fixtures auth)

US-I18N-01 ──▶ US-I18N-02 ──▶ US-I18N-03
```

### Ordre de développement recommandé

```
Semaine 1 :  HEXA-01 + HEXA-02 + DOC-01 (en parallèle, pas de dépendances croisées)
Semaine 2 :  HEXA-03 + HEXA-06 + DOC-02 + TEST-04 + I18N-01
Semaine 3 :  HEXA-04 + TEST-01 + DOC-03 + I18N-02
Semaine 4 :  HEXA-05 + TEST-02 + TEST-03 + DOC-04 + DOC-05 + TEST-05 + I18N-03
```

---

## 11. DÉFINITION OF DONE (DoD)

### Critères universels (toutes les US)

Chaque User Story est considérée DONE seulement si :

- [ ] **Code :** Le code est mergé dans `main` via PR approuvée
- [ ] **Tests :** Les tests définis dans les critères d'acceptation passent (vert)
- [ ] **Coverage :** La couverture globale ne diminue pas après le merge
- [ ] **Linting :** `ruff check` (backend) et `eslint` (frontend) sans erreurs
- [ ] **Types :** `mypy` (backend) et `tsc --noEmit` (frontend) sans erreurs
- [ ] **Review :** Au moins 1 review de code par un autre persona (architecte si logique, QA si test)
- [ ] **Docs :** Si la feature change l'API ou l'architecture, la documentation Docusaurus est mise à jour

### Critères spécifiques Architecture Hexagonale

- [ ] Aucun `select()` SQLAlchemy dans un resolver ou un service
- [ ] Aucun import de `models.py` SQLAlchemy dans un resolver
- [ ] Chaque service peut être instancié avec des mocks (pas de DB réelle requise)

### Critères spécifiques Tests

- [ ] Backend coverage ≥ 85% (mesuré par `pytest --cov`)
- [ ] Frontend coverage ≥ 60% (mesuré par `vitest --coverage`)
- [ ] E2E : 0 test flaky sur 5 runs consécutifs

### Critères spécifiques i18n

- [ ] `git grep -rn '"[A-Za-zÀ-ÿ ]{5,}"' frontend/src/app` ne retourne aucune chaîne de texte utilisateur (seules les constantes techniques autorisées)
- [ ] Les 2 locales (fr, en) sont 100% traduites (aucune clé manquante)

### Critères spécifiques Documentation

- [ ] `npm run build` dans `docs-site/` réussit sans warnings
- [ ] Toutes les pages s'affichent dans Chromium sans erreurs console

---

*Audit rédigé par : Persona #1 Lead Tech + Persona #5 Scrum Master*  
*Validé par : Persona #4 Product Owner (scope MVP confirmé)*  
*Date de création : Avril 2026 | Prochaine révision : fin Sprint 7A*
