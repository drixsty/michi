# 🔧 Setup Git Repository - Michi 道

## 📝 Initialisation Git Locale

```bash
cd michi-app

# Initialiser repo Git
git init

# Ajouter tous les fichiers
git add .

# Premier commit
git commit -m "feat: initial project setup

- Backend FastAPI + Strawberry GraphQL
- Frontend Next.js 14 + Apollo Client
- Docker Compose (PostgreSQL + Redis)
- Auth JWT complete
- Tests unitaires
- Documentation complete (150+ pages)

Closes #1"
```

---

## 🌐 Push vers GitHub

### 1. Créer Repo GitHub
1. Aller sur https://github.com/new
2. Nom du repo : `michi`
3. Description : "🇯🇵 Inventory Forecasting Platform for E-commerce"
4. Visibilité : Private (ou Public)
5. **NE PAS** initialiser avec README (on a déjà)
6. Cliquer "Create repository"

### 2. Lier le Repo Local

```bash
# Ajouter remote origin
git remote add origin https://github.com/VOTRE_USERNAME/michi.git

# Vérifier
git remote -v

# Push
git branch -M main
git push -u origin main
```

---

## 🏷️ Créer un Tag de Release

```bash
# Créer tag v1.0.0 (MVP Phase 0)
git tag -a v1.0.0 -m "v1.0.0 - MVP Phase 0

Features:
- ✅ Backend FastAPI + GraphQL
- ✅ Frontend Next.js 14
- ✅ Auth JWT
- ✅ Docker infrastructure
- ✅ Tests unitaires
- ✅ Documentation (150+ pages)

Status: Ready for Epic 1 development"

# Push le tag
git push origin v1.0.0
```

---

## 📋 Structure des Branches (Recommandé)

### Branches Principales
- `main` : Production-ready code
- `develop` : Development branch

### Branches Features
Format : `feat/nom-feature`

Exemples :
```bash
git checkout -b feat/mock-shopify-generator
git checkout -b feat/out-of-stock-algorithm
git checkout -b feat/dashboard-ui
```

### Workflow Git Flow

```bash
# Créer branche develop
git checkout -b develop
git push -u origin develop

# Créer feature depuis develop
git checkout develop
git checkout -b feat/mock-shopify

# Développer...
git add .
git commit -m "feat(shopify): add mock data generator"

# Push feature
git push origin feat/mock-shopify

# Merger dans develop via Pull Request sur GitHub
# Puis merger develop → main pour releases
```

---

## 🔒 Fichiers Sensibles (.gitignore)

Le `.gitignore` est déjà configuré pour ignorer :

**Backend :**
- `venv/`, `__pycache__/`, `.env`
- `.pytest_cache/`, `htmlcov/`

**Frontend :**
- `node_modules/`, `.next/`, `.env.local`

**Vérifier qu'aucun secret n'est commité :**
```bash
# Vérifier fichiers trackés
git status

# Si .env est listé par erreur
git rm --cached .env
git commit -m "chore: remove .env from git"
```

---

## 📦 Releases GitHub

### Créer une Release v1.0.0

1. Aller sur https://github.com/VOTRE_USERNAME/michi/releases
2. Cliquer "Create a new release"
3. Tag : `v1.0.0`
4. Title : `v1.0.0 - MVP Phase 0 Complete`
5. Description :

```markdown
# 🎉 Michi v1.0.0 - MVP Phase 0

## ✨ Features

### Backend
- ✅ FastAPI + Strawberry GraphQL
- ✅ PostgreSQL 15 + SQLAlchemy 2.0 Async
- ✅ JWT Authentication
- ✅ Alembic Migrations
- ✅ Tests unitaires (pytest)

### Frontend
- ✅ Next.js 14 (App Router)
- ✅ Apollo Client (GraphQL)
- ✅ Tailwind CSS + shadcn/ui
- ✅ Login/Dashboard pages

### Infrastructure
- ✅ Docker Compose (PostgreSQL + Redis)
- ✅ Makefile (commandes utiles)
- ✅ Script seed DB

### Documentation
- ✅ [README.md](../README.md) (9 KB)
- ✅ [prd.md](prd.md) (82 KB - 40+ pages)
- ✅ [architecture.md](architecture.md) (95 KB - 50+ pages)
- ✅ [claude.md](claude.md) (110 KB - 60+ pages)

## 📊 Statistiques

- **Code** : 3 800+ lignes (Python + TypeScript)
- **Tests** : 9 tests (100% pass)
- **Fichiers** : 150+ fichiers
- **Documentation** : 150+ pages

## 🚀 Quickstart

```bash
git clone https://github.com/VOTRE_USERNAME/michi.git
cd michi
make setup      # 3 minutes
make dev-backend
make dev-frontend
# Open http://localhost:3000/login
```

## 🔜 Next Steps

- Epic 1 : Mock Shopify Generator
- Epic 2 : Data Science Algorithms
- Epic 3 : Predictions
- Epic 4 : Dashboard UI

---

**Full Changelog**: https://github.com/VOTRE_USERNAME/michi/commits/v1.0.0
```

6. Cliquer "Publish release"

---

## 🤝 Collaborateurs

### Ajouter Collaborateurs

1. Settings → Collaborators
2. Add people
3. Invite par email

### Protéger Branche Main

1. Settings → Branches
2. Add rule
3. Branch name pattern : `main`
4. Cocher :
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass (Tests CI)
   - ✅ Require branches to be up to date

---

## 🔄 CI/CD GitHub Actions (Optionnel)

Créer `.github/workflows/test.yml` :

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          cd backend
          pip install -r requirements.txt
          pytest

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: |
          cd frontend
          npm install
          npm test
```

---

## 📊 GitHub Project Board (Optionnel)

Créer un board Kanban :

1. Projects → New project
2. Template : "Board"
3. Colonnes :
   - 📋 Backlog
   - 🚧 In Progress
   - 👀 In Review
   - ✅ Done

4. Ajouter Issues pour chaque Epic/US

---

## 🎯 Issues Templates

Créer `.github/ISSUE_TEMPLATE/feature.md` :

```markdown
---
name: Feature Request
about: Nouvelle fonctionnalité
---

## 📝 Description
[Description de la feature]

## 🎯 User Story
En tant que [persona]
Je veux [action]
Afin de [bénéfice]

## ✅ Critères d'Acceptation
- [ ] Critère 1
- [ ] Critère 2

## 📋 Tasks
- [ ] Backend
- [ ] Frontend
- [ ] Tests
- [ ] Documentation
```

---

**Setup Git terminé ! Vous êtes prêt à collaborer ! 道 💜**
