---
id: quickstart
title: Quickstart — 5 minutes
sidebar_label: Quickstart
slug: /guide/quickstart
---

# Démarrage rapide — Michi 道

## Prérequis

```bash
python --version   # 3.11+
node --version     # 18+
docker --version   # 20.10+
```

## Installation automatique

```bash
cd michi-app
make setup
```

Cette commande fait tout :

- Démarre PostgreSQL + Redis (Docker)
- Installe les dépendances backend (pip)
- Installe les dépendances frontend (npm)
- Crée les tables DB (Alembic)
- Seed un utilisateur de développement

**Durée : ~3 minutes**

## Démarrage manuel

```bash
# 1. Services Docker
docker-compose up -d

# 2. Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn src.main:app --reload --port 8000

# 3. Frontend (nouveau terminal)
cd frontend
npm install
npm run dev
```

## URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| GraphQL Playground | http://localhost:8000/graphql |
| API Health | http://localhost:8000/health |

## Compte de test

```
Email    : admin@michi.com
Password : testpassword
```

## Prochaine étape

Connectez une source de données : Shopify, WooCommerce, ou importez un CSV depuis **Réglages > Sources**.
