---
sidebar_position: 1
title: Déploiement & Configuration
---

# Guide de Déploiement et Configuration

Ce guide explique comment mettre en ligne le projet Michi 道 et configurer les environnements de production.

Le projet est divisé en trois applications principales, gérées par un monorepo Turborepo :
1. **API (Backend)** : FastAPI + GraphQL + Base de données PostgreSQL.
2. **Web (Dashboard)** : Application Next.js.
3. **Landing Page** : Site vitrine Next.js.

## Prérequis pour le Déploiement

Avant de déployer en production, vous devez disposer des éléments suivants :
- Un serveur ou PaaS pour héberger le backend (ex: Render, Heroku, AWS).
- Une plateforme d'hébergement front-end pour Next.js (idéalement Vercel).
- Une base de données PostgreSQL managée (ex: Supabase, Neon, AWS RDS).
- Un compte Stripe (pour la facturation).
- Un nom de domaine.

## Variables d'Environnement Globales

Les variables d'environnement suivantes sont cruciales pour le bon fonctionnement de l'application en production.

### Backend (`apps/api/.env`)

```env
ENVIRONMENT=production

# Base de données
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

# Sécurité & Auth
SECRET_KEY=votre_cle_secrete_longue_et_aleatoire
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redirections (Front-end)
FRONTEND_URL=https://app.michi.app

# Stripe (Voir section Stripe)
BILLING_MODE=STRIPE
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

### Web Dashboard (`apps/web/.env.local`)

```env
NEXT_PUBLIC_API_URL=https://api.michi.app
NEXT_PUBLIC_APP_URL=https://app.michi.app
```

### Landing Page (`apps/landing/.env.local`)

```env
NEXT_PUBLIC_API_URL=https://api.michi.app
NEXT_PUBLIC_APP_URL=https://app.michi.app
NEXT_PUBLIC_DEMO_URL=mailto:contact@michi.app
```

## Déploiement sur Vercel (Frontend)

Vercel est la plateforme recommandée pour héberger les applications `web` et `landing`.

1. Connectez votre dépôt GitHub à Vercel.
2. Lors de l'import, sélectionnez le framework **Next.js**.
3. Définissez le **Root Directory** sur `apps/web` (ou `apps/landing`).
4. Dans la section **Build and Output Settings**, Vercel détectera automatiquement qu'il s'agit d'un projet Turborepo.
5. Ajoutez les variables d'environnement (`NEXT_PUBLIC_API_URL`).
6. Déployez !

## Déploiement du Backend (Docker)

Un fichier `docker-compose.yml` est disponible à la racine pour déployer le backend.

```bash
# Construire et lancer le conteneur du backend
docker-compose up -d --build
```

N'oubliez pas d'exécuter les migrations de base de données avant ou pendant le déploiement :
```bash
alembic upgrade head
```
