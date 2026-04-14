---
id: installation
title: Installation détaillée
sidebar_label: Installation
slug: /guide/installation
---

# Installation détaillée

## Variables d'environnement

Créez `backend/.env` :

```env
DATABASE_URL=postgresql+asyncpg://michi:michi@localhost:5432/michi_db
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Google OAuth (optionnel)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Stripe (optionnel)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

## Base de données

```bash
cd backend

# Migrations
alembic upgrade head

# Seed données de démo
python scripts/seed_db.py
```

## Docker Compose complet

```yaml
# docker-compose.yml (extrait)
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: michi_db
      POSTGRES_USER: michi
      POSTGRES_PASSWORD: michi
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

## Tests

```bash
# Backend
cd backend
pytest --cov=src --cov-report=html

# Frontend
cd frontend
npm test
```
