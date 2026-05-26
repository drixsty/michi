# 📚 Michi Documentation - Index

Bienvenue dans la documentation complète du projet Michi 道 !

---

## 🎯 Par Où Commencer ?

### Nouveau sur le projet ?
1. **[README.md](../README.md)** ← Commencez ici
2. **[quickstart.md](quickstart.md)** ← Setup en 5 minutes
3. **[project_summary.md](project_summary.md)** ← Vision globale

### Développeur ?
1. **[architecture.md](architecture.md)** ← Architecture technique
2. **[claude.md](claude.md)** ← Guide agent IA
3. **[tracker.md](tracker.md)** ← Suivi sprints

### Product Owner / PM ?
1. **[prd.md](prd.md)** ← Product Requirements
2. **[tracker.md](tracker.md)** ← Roadmap & metrics

---

## 📖 Documentation Disponible

### 🚀 Démarrage Rapide

#### [README.md](../README.md) (9 KB, 3 pages)
**Contenu :**
- Vue d'ensemble projet
- Installation (backend + frontend)
- Démarrage rapide (3 commandes)
- Architecture
- Tests
- Déploiement

**Quand lire :** Avant toute chose

---

#### [quickstart.md](quickstart.md) (3 KB, 2 pages)
**Contenu :**
- Setup express (5 minutes)
- Commandes Makefile
- Troubleshooting
- Prochaines étapes

**Quand lire :** Pour lancer le projet rapidement

---

#### [project_summary.md](project_summary.md) (12 KB, 8 pages)
**Contenu :**
- Objectif projet
- État actuel (features terminées/à faire)
- Fichiers créés (150+)
- Statistiques (code, tests, docs)
- Roadmap sprints
- Checklist validation MVP

**Quand lire :** Pour comprendre le projet en 10 minutes

---

### 📋 Product & Planning

#### [prd.md](prd.md) (82 KB, 40+ pages)
**Contenu :**
- Vision & objectifs
- User personas (Sophie, Marc)
- 12 User Stories détaillées (Epic 0-4)
- Critères d'acceptation
- Wireframes textuels
- Formules mathématiques
- Métriques de succès
- Roadmap sprint par sprint

**Quand lire :**
- Avant d'implémenter une feature
- Pour rédiger user stories
- Pour comprendre les besoins utilisateurs

**Sections clés :**
- Section 3 : User Personas
- Section 4 : Epics & User Stories (US 0.1 à US 4.6)
- Section 7 : Roadmap (6 sprints)

---

#### [tracker.md](tracker.md) (20+ pages)
**Contenu :**
- Roadmap globale (Sprint 0-6)
- Sprint 0 : ✅ Terminé (infrastructure + auth)
- Sprint 1-6 : User Stories planifiées
- Checklist par sprint
- Métriques vélocité
- Coverage tests
- Backlog Post-MVP
- Rétrospectives

**Quand lire :**
- En début de sprint (planning)
- En fin de sprint (rétrospective)
- Pour tracker avancement

**Comment utiliser :**
- Cocher [x] au fur et à mesure
- Mettre à jour % completion
- Noter blockers

---

### 🧮 Supply Chain Intelligence

#### [supply_chain_intelligence.md](supply_chain_intelligence.md) (~80 KB, 18 sections)
**Contenu :**
- Glossaire complet (termes métier, statistiques, Michi-spécifiques)
- Chaque algorithme expliqué pas-à-pas : OOS Correction, Outlier Detection, Run Rate, Prédiction rupture, ROP Date, Safety Stock, MAPE, ABC, Health Score, Analyse Fournisseurs, KPIs Financiers
- 5 scénarios terrain complets (De l'alerte à la commande fournisseur)
- Positionnement marché & arguments marketing chiffrés
- Calcul ROI pour pitch commercial
- Cartes de référence rapide (toutes les formules, FAQ)
- Références académiques (Silver-Pyke-Peterson, Nahmias, Tukey)

**Quand lire :**
- **Onboarding :** Premier document à lire pour tout nouveau membre de l'équipe Data/Produit
- **Marketing :** Arguments commerciaux et différenciation concurrentielle
- **Développement :** Avant d'implémenter ou modifier un algorithme

**Public cible :** Développeurs, Data Scientists, Product Owners, Marketing, Support client

---

### 🔌 Connecteurs Marketplace

#### [connectors.md](connectors.md)
**Contenu :**
- Architecture hexagonale du module Ingestion
- Contrat BaseConnector (interface + schemas normalisés)
- Plateformes supportées (Shopify, WooCommerce, CSV, Amazon, eBay, Etsy)
- Mode Mock vs Production
- Flux d'ingestion complet (séquence détaillée)
- Stockage sécurisé des credentials (StoreCredential)
- Rate limits & stratégie retry
- Guide pour ajouter un nouveau connecteur
- Tests (mock + VCR)

**Quand lire :** Avant d'intégrer une marketplace ou d'ajouter un connecteur

---

#### [registration_shopify.md](registration_shopify.md)
**Contenu :** Guide pas-à-pas inscription Shopify Partners → Access Token  
**Durée :** 20–30 minutes

---

#### [registration_amazon.md](registration_amazon.md)
**Contenu :** Guide pas-à-pas Amazon SP-API → LWA OAuth, rôles, validation  
**Durée :** 2–5 jours (validation Amazon requise)

---

#### [registration_ebay.md](registration_ebay.md)
**Contenu :** Guide pas-à-pas eBay Developer → OAuth, RuName, expiration 18 mois  
**Durée :** 1–2 jours

---

#### [registration_etsy.md](registration_etsy.md)
**Contenu :** Guide pas-à-pas Etsy API v3 → PKCE OAuth, variantes, expiration 90 jours  
**Durée :** 30 minutes

---

### 🏗️ Technique & Architecture

#### [architecture.md](architecture.md) (95 KB, 50+ pages)
**Contenu :**
- Vue d'ensemble architecture
- **Schéma DB PostgreSQL** (DDL complet)
- **GraphQL schema exhaustif** (types, queries, mutations)
- Resolvers Python (Strawberry)
- Pipeline Data Science (4 algorithmes)
- Frontend Next.js 14
- Sécurité & Performance
- Déploiement (Vercel + Railway)
- Testing strategy
- ADR (décisions techniques)

**Quand lire :**
- Avant de créer un nouveau module
- Pour comprendre le flow de données
- Pour setup la DB
- Pour optimiser performance

**Sections clés :**
- Section 2 : Schéma DB (tables, indexes, DDL)
- Section 3 : API GraphQL (schema complet)
- Section 5 : Pipeline Data Science
- Section 7 : Sécurité & Performance

---

#### [claude.md](claude.md) (25 KB, 20+ pages)
**Contenu :**
- **7 Personas de Claude :**
  1. Lead Tech / Architecte Backend
  2. Data Scientist / ML Engineer
  3. UI/UX Designer / Frontend Dev
  4. Product Owner / Product Manager
  5. Scrum Master / Agile Coach
  6. Security Engineer
  7. DevOps & Performance Engineer
- Quand utiliser quel persona
- **50+ exemples de prompts** structurés
- Workflow collaboration multi-personas

**Quand lire :**
- Avant d'utiliser Claude Code
- Pour savoir quel persona invoquer
- Pour rédiger des prompts efficaces

**Exemples d'usage :**
```
"Persona: Lead Tech - Comment structurer le module notifications ?"
"Persona: Data Scientist - Mon MAPE est à 25%, comment l'améliorer ?"
"Persona: Security Engineer - Audit sécurité endpoint /webhook"
```

---

### 🔧 Setup & Workflows

#### [git_setup.md](git_setup.md) (8 KB, 6 pages)
**Contenu :**
- Initialisation Git locale
- Push vers GitHub
- Créer tags & releases
- Structure branches (Git Flow)
- Fichiers sensibles (.gitignore)
- GitHub Projects (Kanban)
- CI/CD GitHub Actions

**Quand lire :**
- Avant premier commit
- Pour setup repo GitHub
- Pour configurer CI/CD

---

## 🎓 Guides par Rôle

### Si tu es **Product Owner / PM**
1. [prd.md](prd.md) → Vision, user stories, roadmap
2. [tracker.md](tracker.md) → Suivi sprints
3. [project_summary.md](project_summary.md) → État projet

### Si tu es **Développeur Backend**
1. [architecture.md](architecture.md) → Schéma DB, GraphQL
2. [claude.md](claude.md) → Persona #1 (Lead Tech), #2 (Data Scientist)
3. [prd.md](prd.md) → User stories avec critères

### Si tu es **Développeur Frontend**
1. [architecture.md](architecture.md) → Section 6 (Frontend)
2. [claude.md](claude.md) → Persona #3 (UI/UX Designer)
3. [prd.md](prd.md) → Wireframes (section 5)

### Si tu es **Data Scientist**
1. [supply_chain_intelligence.md](supply_chain_intelligence.md) → Formules complètes + cas d'usage terrain
2. [architecture.md](architecture.md) → Section 5 (Pipeline DS)
3. [claude.md](claude.md) → Persona #2 (Data Scientist)
4. [prd.md](prd.md) → Epic 2 (Algorithmes)

### Si tu es **DevOps / SRE**
1. [architecture.md](architecture.md) → Section 8 (Déploiement)
2. [claude.md](claude.md) → Persona #7 (DevOps)
3. [git_setup.md](git_setup.md) → CI/CD GitHub Actions

### Si tu es **Scrum Master**
1. [tracker.md](tracker.md) → Roadmap, vélocité
2. [claude.md](claude.md) → Persona #5 (Scrum Master)
3. [prd.md](prd.md) → Estimations story points

---

## 🔍 Recherche par Sujet

### Connecteurs Marketplace
- [connectors.md](connectors.md) → Architecture + référence technique
- [registration_shopify.md](registration_shopify.md) → Inscription Shopify
- [registration_amazon.md](registration_amazon.md) → Inscription Amazon SP-API
- [registration_ebay.md](registration_ebay.md) → Inscription eBay
- [registration_etsy.md](registration_etsy.md) → Inscription Etsy
- Code : `apps/api/src/modules/ingestion/connectors/`

### Authentification & Sécurité (RBAC)
- [architecture.md](architecture.md) → Section 7 (Auth & RBAC)
- [prd.md](prd.md) → Epic 0 (US 0.1, 0.2)
- [tracker.md](tracker.md) → Sprint 23 (Security Hardening)
- Code : `apps/api/src/modules/auth/`

### Algorithmes Data Science & Supply Chain
- [supply_chain_intelligence.md](supply_chain_intelligence.md) → **Référence complète** (formules, cas d'usage, métier)
- [architecture.md](architecture.md) → Section 5
- [prd.md](prd.md) → Epic 2 (US 2.1, 2.2)
- [tracker.md](tracker.md) → Sprint 3-4

### Dashboard UI
- [prd.md](prd.md) → Epic 4 (US 4.1 à 4.6)
- [tracker.md](tracker.md) → Sprint 6
- Wireframes : PRD section 5

### GraphQL API
- [architecture.md](architecture.md) → Section 3
- Exemples queries : Architecture section 3.2

### Tests
- [architecture.md](architecture.md) → Section 9
- Code : `backend/tests/`, `backend/src/modules/*/tests/`
- Coverage targets : PROGRESS_TRACKER.md

### Déploiement Production
- [architecture.md](architecture.md) → Section 8
- [git_setup.md](git_setup.md) → CI/CD
- Stack : Vercel (frontend) + Railway (backend)

---

## 📊 Statistiques Documentation

| Document | Taille | Pages | Contenu |
|----------|--------|-------|---------|
| README.md | 9 KB | 3 | Vue d'ensemble |
| QUICKSTART.md | 3 KB | 2 | Setup rapide |
| PROJECT_SUMMARY.md | 12 KB | 8 | Récapitulatif |
| prd.md | 82 KB | 40+ | Product Requirements |
| architecture.md | 95 KB | 50+ | Architecture technique |
| **supply_chain_intelligence.md** | **~80 KB** | **18 sections** | **Supply Chain & Algorithmes** |
| claude.md | 25 KB | 20+ | Guide agent IA |
| tracker.md | 15 KB | 15+ | Suivi sprints |
| git_setup.md | 8 KB | 6 | Setup Git/GitHub |
| connectors.md | 18 KB | 10 | Architecture connecteurs |
| registration_shopify.md | 8 KB | 9 | Guide inscription Shopify |
| registration_amazon.md | 10 KB | 10 | Guide inscription Amazon SP-API |
| registration_ebay.md | 10 KB | 11 | Guide inscription eBay |
| registration_etsy.md | 10 KB | 11 | Guide inscription Etsy |
| **Total** | **~385 KB** | **269+** | Documentation complète |

---

## 🆘 Besoin d'Aide ?

### Je cherche...

- **"Comment fonctionne l'algorithme de prévision ?"**  
  → [supply_chain_intelligence.md](supply_chain_intelligence.md)

- **"Comment démarrer le projet ?"**  
  → [quickstart.md](quickstart.md)

- **"Quelle est l'architecture ?"**  
  → [architecture.md](architecture.md)

- **"Quelles features faire en priorité ?"**  
  → [tracker.md](tracker.md)

- **"Comment utiliser Claude Code ?"**  
  → [claude.md](claude.md)

- **"Quels sont les critères d'une US ?"**  
  → [prd.md](prd.md) section 4

- **"Comment déployer en prod ?"**  
  → [architecture.md](architecture.md) section 8

- **"Où est le schéma de la DB ?"**  
  → [architecture.md](architecture.md) section 2

---

## 📞 Contact & Support

**Documentation mise à jour :** 4 Avril 2026  
**Version projet :** v1.0.0 (MVP Phase 0)

Pour toute question :
1. Consulter cette documentation
2. Voir README.md pour support

---

**Navigation rapide :**
- [↑ Retour en haut](#-michi-documentation---index)
- [← Retour au projet](../)

**Bonne lecture ! 道💜**
