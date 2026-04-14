---
id: quickstart
title: Démarrage Rapide
sidebar_label: 🚀 Démarrage Rapide
sidebar_position: 1
---

# 🚀 Michi - Démarrage Ultra-Rapide (5 minutes)

## ⚡ Installation Express

### Prérequis Vérification
```bash
# Vérifier installations
python --version   # Doit être 3.11+
node --version     # Doit être 18+
docker --version   # Doit être 20.10+
```

### Étape 1 : Setup Automatique (Makefile)

```bash
cd michi-app

# Installation complète (services + dépendances + seed DB)
make setup
```

**Cette commande fait TOUT :**
- ✅ Démarre PostgreSQL + Redis (Docker)
- ✅ Installe les dépendances (npm root & workspaces)
- ✅ Installe les dépendances backend (apps/api/requirements.txt)
- ✅ Crée les tables et les migrations DB
- ✅ Seed les données de démo v2 (SaaS Multi-Tenant)

---

### Étape 2 : Lancement des Services

Il est recommandé d'utiliser des terminaux séparés pour chaque service :

| Service | Commande | URL |
|---------|----------|-----|
| **API Backend** | `make api` | [http://localhost:8000/graphql](http://localhost:8000/graphql) |
| **PWA Frontend** | `make web` | [http://localhost:3000](http://localhost:3000) |
| **Documentation** | `make docs` | [http://localhost:3001](http://localhost:3001) |

---

### Étape 3 : Authentification

Ouvrir [http://localhost:3000/login](http://localhost:3000/login).

**Comptes de Test :**
- **Email :** `dev@michi.com`
- **Password :** `password123` (ou `michi123`)

---

## 🔐 Variables d'Environnement

Le projet utilise des fichiers `.env` pour la configuration locale.

### Backend (`apps/api/.env`)
- `DATABASE_URL` : Connexion PostgreSQL.
- `SECRET_KEY` : Clé de signature des tokens JWT.
- `STRIPE_SECRET_KEY` : Clé API Stripe (optionnel pour mock).

### Frontend (`apps/web/.env.local`)
- `NEXT_PUBLIC_GRAPHQL_URL` : URL de l'API (défaut: `http://localhost:8000/graphql`).

---

## 📋 Commandes Essentielles

| Commande | Action |
|----------|--------|
| `make schema` | Exporte le schéma GraphQL (SDL) |
| `make test` | Lance tous les tests (API + Web + UI) |
| `make docker-up` | Redémarre uniquement la base de données |
| `make clean` | Supprime `node_modules` et `__pycache__` |

---

## 📁 Structure Monorepo

```text
michi-app/
├── apps/
│   ├── api/            # FastAPI Backend
│   └── web/            # Next.js 14 Web App
├── packages/
│   ├── types/          # Types partagés & GraphQL Codegen
│   └── ui/             # Design System (shadcn/ui)
├── docs-site/          # Site Docusaurus
└── Makefile            # Orchestrateur root
```

---

**Bon développement ! 道 💜**
