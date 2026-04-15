# Michi 道 - Inventory Forecasting Platform

**Stoppez les ruptures de stock et les surstocks coûteux — sans Excel, sans data analyst**

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-purple)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Next.js](https://img.shields.io/badge/next.js-14-black)

</div>

---

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Stack Technique](#stack-technique)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Démarrage Rapide](#démarrage-rapide)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Tests](#tests)
- [Déploiement](#déploiement)
- [Contribuer](#contribuer)

---

## 🎯 Vue d'Ensemble

Michi est une plateforme SaaS de prévision de stocks pour e-commerces mode & beauté (50-500 SKU, 50K-500K€ CA/an).

### Problème Résolu
- **Ruptures de stock** : -40% de ruptures grâce à l'IA prédictive
- **Surstocks coûteux** : Optimisation des commandes fournisseur
- **Gestion Excel chronophage** : Interface no-code intuitive

### MVP Features
- ✅ Authentification JWT
- ✅ GraphQL API
- 🚧 Génération de données Mock (Shopify)
- 🚧 Algorithmes de nettoyage (Out-of-Stock correction)
- 🚧 Prédictions de rupture
- 🚧 Recommandations de commande
- 🚧 Dashboard avec KPIs

---

## 🛠️ Stack Technique

### Backend
- **Framework** : FastAPI (Python 3.11+)
- **API** : Strawberry GraphQL
- **Database** : PostgreSQL 15+ (SQLAlchemy 2.0 Async)
- **Auth** : JWT (python-jose + passlib)
- **Data Science** : Pandas, NumPy, scikit-learn

### Frontend
- **Framework** : Next.js 14 (App Router)
- **GraphQL Client** : Apollo Client
- **Styling** : Tailwind CSS + shadcn/ui
- **Language** : TypeScript

### Infrastructure
- **Database** : PostgreSQL 15
- **Cache** : Redis 7 (optionnel)
- **Containerization** : Docker + Docker Compose
- **Migrations** : Alembic

---

## 📦 Prérequis

- **Python** : 3.11+
- **Node.js** : 18+
- **Docker** : 20.10+ (pour PostgreSQL/Redis)
- **npm** : 9+

---

## 🚀 Installation

### 1. Cloner le Projet

```bash
git clone https://github.com/votreuser/michi.git
cd michi
```

### 2. Backend Setup (`apps/api`)

```bash
cd apps/api

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Copier .env
cp .env.example .env
```

### 3. Frontend Setup (`apps/web`)

```bash
cd apps/web

# Installer dépendances
npm install

# Copier .env.local
cp .env.local.example .env.local
```

### 4. Démarrer les Services Docker

```bash
cd ..

# Démarrer PostgreSQL + Redis
docker-compose up -d

# Vérifier que les services tournent
docker-compose ps
```

### 5. Initialiser la Database

```bash
cd apps/api

# Créer tables + seed user de dev
python scripts/seed_dev_data.py
```

**Output attendu :**
```
✅ Tables créées
✅ User de développement créé !
   Email: dev@michi.com
   Password: password123
   User ID: <uuid>
   Shop ID: <uuid>
```

---

## 🎬 Démarrage Rapide

### Terminal 1 : Backend

```bash
cd apps/api
source venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend disponible sur :**
- API : http://localhost:8000
- GraphQL Playground : http://localhost:8000/graphql
- Health Check : http://localhost:8000/health
- Docs : http://localhost:8000/docs

### Terminal 2 : Frontend

```bash
cd apps/web
npm run dev
```

**Frontend disponible sur :**
- App : http://localhost:3000
- Login : http://localhost:3000/login

### Terminal 3 : Logs Docker (optionnel)

```bash
docker-compose logs -f
```

---

## 🔐 Connexion
Ouvrir [http://localhost:3000/login](http://localhost:3000/login)

**Comptes de développement (Seed Standard) :**

| Email | Password | Plan | Rôle |
|-------|----------|------|------|
| `dev@michi.com` | `michi123` / `password123` | ENTERPRISE | ADMIN |
| `pro@michi.com` | `password123` | PRO | ADMIN |
| `basic@michi.com` | `password123` | BASIC | ADMIN |
| `late@michi.com` | `password123` | PRO (Past Due) | ADMIN |

Après login, vous serez redirigé vers `/dashboard`.

---

## 🏗️ Architecture

### Structure des Dossiers

```
michi-app/
├── apps/
│   ├── api/                   # Backend (FastAPI + DDD)
│   │   ├── src/
│   │   │   ├── core/          # Infrastructure Partagée
│   │   │   ├── modules/       # Domaines métiers isolés
│   │   │   │   ├── domain/        # Entities, Ports, Logic
│   │   │   │   ├── application/   # Services, Use Cases
│   │   │   │   └── infrastructure/# Persistence, Adapters
│   │   │   └── main.py
│   │   └── tests/
│   ├── web/                   # Frontend (Next.js 14)
│   └── mobile/                # Application Mobile (React Native/Expo)
│
├── packages/
│   ├── core/                  # Shared Kernel (DB, Types, Utils)
│   ├── types/                 # Typages TypeScript partagés
│   └── ui/                    # Design System (shadcn/ui)
│
├── docker-compose.yml         # Services (PostgreSQL + Redis)
└── README.md
```

### Flux de Données

```
┌──────────────┐
│   Frontend   │  Next.js 14 (App Router)
│  (port 3000) │
└──────┬───────┘
       │ GraphQL (Apollo Client)
       ▼
┌──────────────┐
│   Backend    │  FastAPI + Strawberry GraphQL
│  (port 8000) │
└──────┬───────┘
       │ SQLAlchemy Async
       ▼
┌──────────────┐
│  PostgreSQL  │  Database
│  (port 5432) │
└──────────────┘
```

---

## 📚 Documentation

### Documents Techniques

- **PRD Complet** : `docs/prd.md` (40+ pages)
- **Architecture** : `docs/architecture.md` (50+ pages)
- **Instructions Claude Code** : `docs/claude.md` (60+ pages)

### API GraphQL

**Exemple Query :**
```graphql
query {
  me {
    id
    email
    shopId
  }
}
```

**Exemple Mutation :**
```graphql
mutation {
  login(input: {
    email: "dev@michi.com"
    password: "password123"
  }) {
    token
    user {
      id
      email
    }
  }
}
```

**Documentation Interactive :**
- GraphQL Playground : http://localhost:8000/graphql
- OpenAPI Docs : http://localhost:8000/docs

---

## 🧪 Tests

### Backend (pytest)

```bash
cd apps/api

# Tous les tests
python -m pytest tests/unit

# Avec coverage
python -m pytest tests/unit --cov=src --cov-report=html
```

### Frontend (Vitest + Playwright)

```bash
cd apps/web

# Unit tests
npm test

# E2E tests
npm run test:e2e
```

### Coverage Targets

| Module       | Unit | Integration | E2E | Total |
|--------------|------|-------------|-----|-------|
| auth         | 95%  | 80%         | 60% | 85%   |
| inventory    | 90%  | 85%         | 70% | 85%   |
| forecasting  | 95%  | 90%         | 50% | 90%   |

---

## 🚢 Déploiement

### Production Stack

- **Frontend** : Vercel (Edge Network)
- **Backend** : Railway / Render
- **Database** : Railway PostgreSQL / Supabase
- **Redis** : Upstash Redis

### Variables d'Environnement (Production)

**Backend :**
```bash
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=<openssl rand -hex 32>
ENVIRONMENT=production
CORS_ORIGINS=https://michi.vercel.app
USE_MOCK_SHOPIFY=false  # Une fois Shopify API intégré
```

**Frontend :**
```bash
NEXT_PUBLIC_GRAPHQL_URL=https://api.michi.app/graphql
```

### CI/CD (GitHub Actions)

Workflow automatique sur `push` vers `main` :
1. Run tests (backend + frontend)
2. Build frontend (Next.js)
3. Deploy frontend → Vercel
4. Deploy backend → Railway

---

## 🤝 Contribuer

### Workflow Git

```bash
# Créer une branche
git checkout -b feat/my-feature

# Faire vos changements
git add .
git commit -m "feat(module): description"

# Push
git push origin feat/my-feature

# Créer une Pull Request sur GitHub
```

### Conventional Commits

Format : `<type>(<scope>): <subject>`

**Types :**
- `feat`: Nouvelle feature
- `fix`: Bug fix
- `refactor`: Refactoring code
- `test`: Ajout/modification tests
- `docs`: Documentation
- `chore`: Maintenance

**Exemples :**
```
feat(forecasting): add out-of-stock correction algorithm
fix(auth): prevent JWT token expiry race condition
test(inventory): add unit tests for ProductService
docs(readme): update installation instructions
```

---

## 📄 License

MIT License - voir [LICENSE](LICENSE) pour détails.

---

## 👥 Équipe

- **Product Owner** : [Votre Nom]
- **Tech Lead** : [Votre Nom]
- **Data Scientist** : [Votre Nom]

---

## 🙏 Remerciements

- **Inspirations Design** : Linear, Stripe, Notion
- **Stack Inspirations** : Shopify, GitHub, Stripe API

---

## 📞 Support

- **Email** : support@michi.ai
- **Documentation** : https://docs.michi.ai
- **Issues** : https://github.com/votreuser/michi/issues

---

<div align="center">

**Michi 道 — Le chemin vers la croissance prédictive**

Made with 💜 in Paris

</div>
