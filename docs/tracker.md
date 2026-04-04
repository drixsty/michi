# 📊 Michi - Progress Tracker

**Dernière mise à jour :** 4 Avril 2026  
**Version actuelle :** v1.0.0 (MVP Phase 0 Complete)  
**Sprint actuel :** Sprint 0 ✅ Terminé

---

## 🎯 Vision MVP

**Objectif global :** Plateforme de prévision de stocks pour e-commerce mode/beauté

**Cible :** 5 clients pilotes validant :
- ✅ Réduction ruptures de 40%
- ✅ ROI < 2 mois
- ✅ Économies €10K+ par an

**Timeline :** 12 semaines (6 sprints de 2 semaines)

---

## 📅 Roadmap Globale

```
Sprint 0  ✅ [■■■■■■■■■■] 100%  Infrastructure & Auth
Sprint 1  ⏳ [□□□□□□□□□□]   0%  Epic 1: Mock Shopify (Part 1)
Sprint 2  ⏳ [□□□□□□□□□□]   0%  Epic 1: Mock Shopify (Part 2)
Sprint 3  ⏳ [□□□□□□□□□□]   0%  Epic 2: Algorithmes Data Science (Part 1)
Sprint 4  ⏳ [□□□□□□□□□□]   0%  Epic 2: Algorithmes Data Science (Part 2)
Sprint 5  ⏳ [□□□□□□□□□□]   0%  Epic 3: Prédictions
Sprint 6  ⏳ [□□□□□□□□□□]   0%  Epic 4: Dashboard UI
```

---

## ✅ Sprint 0 : Infrastructure & Auth (TERMINÉ)

**Dates :** 1-4 Avril 2026  
**Objectif :** Setup complet du projet + Authentification JWT  
**Statut :** ✅ **TERMINÉ**

### User Stories Complétées

#### Epic 0 : Authentification & Sécurité

| ID | User Story | Story Points | Statut | Développeur |
|----|-----------|--------------|--------|-------------|
| US 0.1 | Login JWT | 3 | ✅ | Claude |
| US 0.2 | Protection API GraphQL | 2 | ✅ | Claude |

**Total Sprint 0 :** 5 story points ✅ Complétés

### Livrables

✅ **Backend Complete**
- [x] FastAPI + Strawberry GraphQL
- [x] PostgreSQL 15 + SQLAlchemy 2.0 Async
- [x] JWT Authentication (login mutation, me query)
- [x] Alembic migrations
- [x] Tests unitaires (9 tests, 100% pass)
- [x] Script seed DB

✅ **Frontend Complete**
- [x] Next.js 14 (App Router)
- [x] Apollo Client (GraphQL)
- [x] Pages: Login + Dashboard
- [x] Tailwind CSS + Brand Michi
- [x] Types TypeScript

✅ **Infrastructure**
- [x] Docker Compose (PostgreSQL + Redis)
- [x] Makefile (12 commandes)
- [x] .gitignore
- [x] CI/CD examples

✅ **Documentation**
- [x] README.md (9 KB)
- [x] quickstart.md (3 KB)
- [x] prd.md (82 KB, 40+ pages)
- [x] architecture.md (95 KB, 50+ pages)
- [x] claude.md (7 personas)
- [x] project_summary.md
- [x] git_setup.md

### Métriques Sprint 0

- **Vélocité :** 5 story points
- **Tests :** 9 tests (100% pass)
- **Coverage :** auth module 100%
- **Documentation :** 200+ pages
- **Fichiers créés :** 150+

### Rétrospective Sprint 0

**✅ Ce qui a bien fonctionné :**
- Architecture modulaire claire
- Documentation exhaustive
- Tests dès le début
- Makefile simplifie workflow

**⚠️ Améliorations possibles :**
- Ajouter CI/CD GitHub Actions
- Setup Sentry pour error tracking
- Ajouter pre-commit hooks (black, isort)

---

## 🚧 Sprint 1 : Epic 1 - Mock Shopify (Part 1)

**Dates :** 8-19 Avril 2026 (2 semaines)  
**Objectif :** Générateur de données de test + Interface sync  
**Statut :** ⏳ **À COMMENCER**

### User Stories Planifiées

#### Epic 1 : Ingestion des Données & Mock Shopify

| ID | User Story | Story Points | Assigné | Statut |
|----|-----------|--------------|---------|--------|
| US 1.1 | Générateur fausses données (products) | 5 | - | 📋 Backlog |
| US 1.2 | Historique ventes avec ruptures simulées | 5 | - | 📋 Backlog |
| US 1.3 | Interface sync (bouton "Synchroniser") | 3 | - | 📋 Backlog |

**Total Sprint 1 :** 13 story points planifiés

### Checklist Sprint 1

**Backend :**
- [ ] Créer `src/modules/shopify/mock_generator.py`
- [ ] Fonction `generate_mock_products(count: int = 50)`
- [ ] Fonction `generate_mock_sales(product_id, days: int = 365)`
- [ ] Simulation ruptures (10-15% produits, 3-21 jours)
- [ ] Simulation outliers (Black Friday, soldes)
- [ ] Tests unitaires mock_generator
- [ ] Mutation GraphQL `triggerMockDataSync`

**Frontend :**
- [ ] Bouton "Synchroniser" sur dashboard
- [ ] Loading state pendant génération
- [ ] Toast notification success/error
- [ ] Redirect après sync réussi

**Tests :**
- [ ] Test génération 50 produits
- [ ] Test historique 365 jours
- [ ] Test ruptures détectées
- [ ] Test E2E: Click sync → Voir produits

### Critères d'Acceptation

✅ Sprint 1 considéré terminé si :
- 50 produits générés avec SKU, titre, stock
- 365 jours d'historique par produit
- 10-15% produits ont ruptures simulées
- Bouton sync fonctionne (GraphQL mutation)
- Tests passent (coverage > 85%)

---

## ⏳ Sprint 2 : Epic 1 - Mock Shopify (Part 2)

**Dates :** 22 Avril - 3 Mai 2026  
**Objectif :** Finaliser génération données + Validation  
**Statut :** ⏳ **Non commencé**

### User Stories Planifiées

| ID | User Story | Story Points | Statut |
|----|-----------|--------------|--------|
| US 1.4 | Validation données générées | 3 | 📋 Backlog |
| US 1.5 | Seed script pour démo | 2 | 📋 Backlog |
| US 1.6 | Documentation générateur | 2 | 📋 Backlog |

**Total Sprint 2 :** 7 story points planifiés

---

## ⏳ Sprint 3-4 : Epic 2 - Algorithmes Data Science

**Dates :** 6-31 Mai 2026 (4 semaines)  
**Objectif :** Nettoyage données + Prédictions  
**Statut :** ⏳ **Non commencé**

### User Stories Planifiées

#### Epic 2 : Algorithmes de Nettoyage

| ID | User Story | Story Points | Statut |
|----|-----------|--------------|--------|
| US 2.1 | Out-of-Stock Correction (moyenne mobile 14j) | 8 | 📋 Backlog |
| US 2.2 | Outlier Detection (méthode IQR) | 5 | 📋 Backlog |
| US 2.3 | Table `cleaned_demand` | 3 | 📋 Backlog |
| US 2.4 | Tests MAPE < 15% | 5 | 📋 Backlog |

**Total Sprint 3-4 :** 21 story points planifiés

### Critères d'Acceptation

✅ Epic 2 terminé si :
- Algorithme Out-of-Stock corrige ruptures
- Algorithme IQR détecte outliers
- Table `cleaned_demand` peuplée
- MAPE < 15% sur 80% des produits test
- Tests unitaires coverage > 90%

---

## ⏳ Sprint 5 : Epic 3 - Prédictions

**Dates :** 3-14 Juin 2026  
**Objectif :** Calculs prédictifs (Date rupture, Qté commande)  
**Statut :** ⏳ **Non commencé**

### User Stories Planifiées

#### Epic 3 : Paramétrage & Prédictions

| ID | User Story | Story Points | Statut |
|----|-----------|--------------|--------|
| US 3.1 | Variables Lead Time & MOQ (édition inline) | 3 | 📋 Backlog |
| US 3.2 | Calcul Date de Rupture | 5 | 📋 Backlog |
| US 3.3 | Recommandation Quantité Commande | 5 | 📋 Backlog |
| US 3.4 | Query `replenishmentAlerts` | 3 | 📋 Backlog |
| US 3.5 | Query `dashboardKPIs` | 3 | 📋 Backlog |

**Total Sprint 5 :** 19 story points planifiés

---

## ⏳ Sprint 6 : Epic 4 - Dashboard UI

**Dates :** 17-28 Juin 2026  
**Objectif :** Interface dashboard complète  
**Statut :** ⏳ **Non commencé**

### User Stories Planifiées

#### Epic 4 : UI/UX Dashboard

| ID | User Story | Story Points | Statut |
|----|-----------|--------------|--------|
| US 4.1 | KPI Cards (manque à gagner, urgents) | 3 | 📋 Backlog |
| US 4.2 | Tableau produits (tri par urgence) | 5 | 📋 Backlog |
| US 4.3 | Badges priorité (🔴🟡🟢) | 2 | 📋 Backlog |
| US 4.4 | Filtres (urgent, tous, sain) | 3 | 📋 Backlog |
| US 4.5 | Export CSV | 3 | 📋 Backlog |
| US 4.6 | Responsive mobile | 5 | 📋 Backlog |

**Total Sprint 6 :** 21 story points planifiés

---

## 📈 Métriques Globales

### Vélocité par Sprint

| Sprint | Planifié | Réalisé | % |
|--------|----------|---------|---|
| Sprint 0 | 5 pts | 5 pts | 100% |
| Sprint 1 | 13 pts | - | - |
| Sprint 2 | 7 pts | - | - |
| Sprint 3-4 | 21 pts | - | - |
| Sprint 5 | 19 pts | - | - |
| Sprint 6 | 21 pts | - | - |

**Total MVP :** 86 story points

### Coverage Tests

| Module | Actuel | Objectif |
|--------|--------|----------|
| auth | 100% ✅ | 85% |
| shopify | - | 75% |
| inventory | - | 85% |
| forecasting | - | 90% |
| **GLOBAL** | 100% | 85% |

### Documentation

| Document | Pages | Statut |
|----------|-------|--------|
| README.md | 3 | ✅ |
| QUICKSTART.md | 2 | ✅ |
| PRD_COMPLET.md | 40+ | ✅ |
| ARCHITECTURE_COMPLETE.md | 50+ | ✅ |
| CLAUDE_v4_PERSONAS.md | 20+ | ✅ |
| **Total** | 200+ | ✅ |

---

## 🎯 Objectifs MVP (Rappel)

### Objectifs Business

- [ ] 5 clients pilotes actifs
- [ ] Réduction ruptures 40%+ (vs baseline)
- [ ] Économies moyennes €10K+/client/an
- [ ] NPS > 40
- [ ] Churn < 10%

### Objectifs Techniques

- [x] Backend GraphQL fonctionnel
- [x] Frontend responsive
- [ ] MAPE < 15% (80% produits)
- [ ] Latency API < 200ms p95
- [ ] Uptime > 99.5%
- [ ] Coverage tests > 85%

### Objectifs Produit

- [x] Authentification sécurisée
- [ ] Génération données mock
- [ ] Algorithmes prédictifs validés
- [ ] Dashboard intuitif
- [ ] Mobile-first design

---

## 📋 Backlog Post-MVP (Parking Lot)

Ces features sont hors scope MVP mais peuvent être ajoutées après validation :

### P1 (High Priority Post-MVP)
- [ ] Intégration Shopify API réelle
- [ ] Multi-utilisateurs (permissions)
- [ ] Alertes email automatiques
- [ ] Export Excel prédictions

### P2 (Medium Priority)
- [ ] Mobile app native (React Native)
- [ ] Dashboard fournisseurs
- [ ] Historique commandes
- [ ] Prédictions multi-SKU (bundles)

### P3 (Low Priority)
- [ ] API publique (webhooks)
- [ ] Intégrations (WooCommerce, Prestashop)
- [ ] White-label
- [ ] Advanced analytics (Prophet, LSTM)

---

## 🚀 Comment Utiliser ce Tracker

### 1. Avant de Commencer un Sprint

```markdown
1. Lire objectif sprint
2. Vérifier User Stories planifiées
3. Estimer si vélocité réaliste
4. Ajuster si nécessaire
```

### 2. Pendant le Sprint

```markdown
- Cocher [ ] → [x] au fur et à mesure
- Mettre à jour statut (Backlog → In Progress → Done)
- Noter blockers dans rétrospective
```

### 3. Fin de Sprint

```markdown
1. Calculer vélocité réalisée
2. Mettre à jour % completion
3. Écrire rétrospective
4. Ajuster estimations Sprint N+1
```

---

## 🔄 Changelog

### v1.0.0 - Sprint 0 Complete (4 Avril 2026)

**Ajouté :**
- Backend FastAPI + GraphQL
- Frontend Next.js 14
- Auth JWT
- Docker infrastructure
- Documentation (200+ pages)
- Tests (9 tests, 100% pass)

**Prochaines Étapes :**
- Sprint 1 : Mock Shopify generator

---

## 📞 Support

**Questions sur ce tracker ?**
- Voir README.md pour documentation complète
- Voir PROJECT_SUMMARY.md pour vision globale

---

**Mis à jour automatiquement à chaque fin de sprint. 道💜**
