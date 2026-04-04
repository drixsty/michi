# 🎯 Michi - Templates de Prompts pour Claude Code

**Guide complet des prompts prêts à copier-coller pour accélérer le développement avec Claude Code.**

---

## 📋 Table des Matières

1. [Prompts Sprint Planning](#1-prompts-sprint-planning)
2. [Prompts Développement Backend](#2-prompts-développement-backend)
3. [Prompts Développement Frontend](#3-prompts-développement-frontend)
4. [Prompts Data Science](#4-prompts-data-science)
5. [Prompts Code Review & Quality](#5-prompts-code-review--quality)
6. [Prompts Debugging](#6-prompts-debugging)
7. [Prompts Documentation](#7-prompts-documentation)

---

## 1. Prompts Sprint Planning

### 📅 Planifier un Sprint

```
Persona: Scrum Master

Contexte: Je commence Sprint [N] avec objectif: [Epic X complet].

User Stories planifiées:
- US X.1: [Description] (? story points)
- US X.2: [Description] (? story points)
- US X.3: [Description] (? story points)

Question: 
1. Estime les story points pour chaque US (Fibonacci: 1,2,3,5,8,13)
2. Décompose chaque US en tâches de 0.5-2 jours
3. Identifie risques/blockers potentiels
4. Vérifie si vélocité réaliste pour 2 semaines

Contraintes:
- Vélocité Sprint 0: [X] story points
- Équipe: [X] développeur(s)
```

**Exemple concret :**
```
Persona: Scrum Master

Contexte: Je commence Sprint 1 avec objectif: Epic 1 (Mock Shopify) complet.

User Stories planifiées:
- US 1.1: Générateur produits (? pts)
- US 1.2: Historique ventes avec ruptures (? pts)
- US 1.3: Interface sync bouton (? pts)

Question: Estime et décompose.

Contraintes:
- Vélocité Sprint 0: 5 story points
- Équipe: 1 développeur
```

---

### ✅ Écrire une User Story

```
Persona: Product Owner

Contexte: Je veux ajouter feature [DESCRIPTION FEATURE].

Impact business attendu:
- [Impact 1]
- [Impact 2]

Question: Rédige une User Story au format:

En tant que [persona]
Je veux [action]
Afin de [bénéfice]

Critères d'acceptation:
- [ ] Critère 1
- [ ] Critère 2
- [ ] Critère 3

Estimation: [Story points] pts
```

**Exemple concret :**
```
Persona: Product Owner

Contexte: Ajouter possibilité de modifier Lead Time d'un produit.

Impact business:
- User peut adapter délai fournisseur
- Prédictions plus précises

Question: Rédige US complète.
```

---

## 2. Prompts Développement Backend

### 🏗️ Créer un Nouveau Module

```
Persona: Lead Tech

Contexte: Je veux créer un nouveau module "[NOM_MODULE]" pour gérer [FONCTIONNALITÉ].

Besoins:
- [Besoin 1]
- [Besoin 2]

Question: Donne-moi:
1. Structure dossiers (models, schemas, service, resolvers, tests)
2. Modèle SQLAlchemy avec relations
3. Schema Pydantic
4. Service avec méthodes CRUD
5. Resolver GraphQL
6. Tests unitaires (2-3 exemples)

Contraintes:
- Domain-Driven Design
- Async Python (FastAPI + SQLAlchemy 2.0)
- GraphQL-only API
```

**Exemple concret :**
```
Persona: Lead Tech

Contexte: Créer module "notifications" pour alertes email rupture.

Besoins:
- Table notifications (product_id, user_id, sent_at, type)
- Envoi email async (Celery)
- Query listNotifications

Question: Structure complète du module.
```

---

### 📊 Créer un Endpoint GraphQL

```
Persona: Lead Tech

Contexte: Ajouter query/mutation GraphQL:

[QUERY/MUTATION]: [Description]

Input: [Params]
Output: [Type retourné]

Question: Donne-moi:
1. Type Strawberry GraphQL
2. Resolver Python
3. Service method
4. Test unitaire
5. Exemple query GraphQL

Contraintes:
- Validation Pydantic
- Error handling (MichiException)
- Auth required (JWT)
```

**Exemple concret :**
```
Persona: Lead Tech

Mutation: updateLeadTime(productId: ID!, leadTime: Int!): Product

Input: productId, leadTime (1-90 jours)
Output: Product updated

Question: Code complet + test.
```

---

## 3. Prompts Développement Frontend

### 🎨 Créer une Page Next.js

```
Persona: UI/UX Designer

Contexte: Créer page [NOM_PAGE] pour [OBJECTIF].

Fonctionnalités:
- [Feature 1]
- [Feature 2]

UI Requirements:
- Mobile-first
- Tailwind CSS
- shadcn/ui components
- Accessibilité WCAG AA

Question: Donne-moi:
1. Composant Next.js 14 (App Router)
2. Hooks custom pour data fetching (Apollo)
3. Types TypeScript
4. Responsive design (mobile → desktop)

Inspiration: [Linear / Stripe / Notion]
```

**Exemple concret :**
```
Persona: UI/UX Designer

Contexte: Page "Produits" listant tous les produits.

Fonctionnalités:
- Tableau avec tri
- Filtres (urgent/tous/sain)
- Search bar
- Badges priorité

UI: Mobile-first, Tailwind, shadcn/ui Table

Question: Code complet page + composants.
```

---

### 🧩 Créer un Composant React

```
Persona: UI/UX Designer

Contexte: Créer composant [NOM_COMPOSANT] pour [USAGE].

Props:
- [prop1]: [type] - [description]
- [prop2]: [type] - [description]

States:
- [state1]
- [state2]

Question: Donne-moi:
1. Composant React TypeScript
2. Styles Tailwind
3. Gestion states
4. Props validation
5. Exemple usage

Contraintes:
- Responsive
- Accessible (ARIA labels)
- Dark mode compatible
```

**Exemple concret :**
```
Persona: UI/UX Designer

Composant: ProductCard pour afficher un produit.

Props:
- product: Product
- onUpdate: (id, data) => void

States: isEditing, isLoading

Question: Code complet + exemple.
```

---

## 4. Prompts Data Science

### 🧮 Implémenter un Algorithme

```
Persona: Data Scientist

Contexte: Implémenter algorithme [NOM_ALGO] pour [OBJECTIF].

Input: DataFrame avec colonnes [col1, col2, ...]
Output: DataFrame avec colonnes [col_result1, ...]

Formule mathématique:
[FORMULE]

Hypothèses:
- [Hypothèse 1]
- [Hypothèse 2]

Question: Donne-moi:
1. Fonction Python (Pandas vectorisé)
2. Gestion edge cases (NaN, division par zéro, etc.)
3. Tests unitaires (3-5 cas)
4. Docstring avec formule

Critères de succès:
- Performance: < [X] secondes pour 1000 produits
- Précision: MAPE < [Y]%
```

**Exemple concret :**
```
Persona: Data Scientist

Algorithme: Out-of-Stock Correction

Input: daily_sales_logs (product_id, date, units_sold, end_of_day_stock)
Output: + theoretical_units_sold

Formule: Si stock=0, theoretical = moyenne_mobile_14j_avant

Hypothèses:
- Pas de ventes futures connues
- Distribution normale des ventes

Question: Code complet + tests.

Critères: < 2s pour 50 produits, MAPE < 15%
```

---

### 📉 Optimiser Performance Algorithme

```
Persona: Data Scientist

Contexte: Mon algorithme [NOM] est trop lent.

Performance actuelle: [X] secondes pour [Y] lignes
Objectif: < [Z] secondes

Profiling:
- [Bottleneck 1]: [X]% du temps
- [Bottleneck 2]: [Y]% du temps

Code actuel:
[CODE]

Question: Comment optimiser ?
Propose 2-3 techniques (vectorisation, chunking, multiprocessing).
```

**Exemple concret :**
```
Persona: Data Scientist

Algorithme: Out-of-Stock Correction

Actuel: 8s pour 1000 produits (objectif < 2s)

Profiling:
- Boucle for sur produits: 60%
- Rolling mean calcul: 30%

Question: Optimisation avec Pandas vectorisé.
```

---

## 5. Prompts Code Review & Quality

### 🔍 Code Review Sécurité

```
Persona: Security Engineer

Contexte: Code review sécurité du module/endpoint [NOM].

Code:
[CODE]

Question: Audit OWASP Top 10:
1. Injection (SQL, NoSQL, Command)
2. Broken Authentication
3. Sensitive Data Exposure
4. XML External Entities (XXE)
5. Broken Access Control
6. Security Misconfiguration
7. Cross-Site Scripting (XSS)
8. Insecure Deserialization
9. Using Components with Known Vulnerabilities
10. Insufficient Logging & Monitoring

Pour chaque vulnérabilité trouvée:
- Sévérité (Critical/High/Medium/Low)
- Description
- Fix proposé
```

**Exemple concret :**
```
Persona: Security Engineer

Endpoint: POST /webhooks/shopify

Code:
@app.post("/webhooks/shopify")
async def webhook(data: dict):
    await db.execute(insert(Sales).values(**data))
    return {"ok": True}

Question: Audit sécurité complet.
```

---

### 🧪 Générer des Tests

```
Persona: Lead Tech

Contexte: J'ai implémenté [FEATURE] mais pas encore de tests.

Code:
[CODE]

Question: Génère tests unitaires pytest:
1. Test cas nominal (happy path)
2. Test edge cases (invalid input, None, etc.)
3. Test error handling
4. Fixtures si nécessaire

Contraintes:
- Coverage > 85%
- Fixtures réutilisables (conftest.py)
- Assertions claires
```

**Exemple concret :**
```
Persona: Lead Tech

Feature: AuthService.login()

Code:
async def login(self, email: str, password: str):
    user = await get_user(email)
    if not verify_password(password, user.hashed_password):
        raise UnauthenticatedException()
    return create_token(user)

Question: Tests complets.
```

---

## 6. Prompts Debugging

### 🐛 Debugger une Erreur

```
Persona: Lead Tech

Contexte: J'ai une erreur [TYPE_ERREUR] dans [MODULE/FONCTION].

Stack trace:
[STACK_TRACE]

Code concerné:
[CODE]

Comportement attendu: [DESCRIPTION]
Comportement actuel: [DESCRIPTION]

Question:
1. Quelle est la cause root ?
2. Comment fix ?
3. Comment éviter à l'avenir (test, validation, etc.) ?
```

**Exemple concret :**
```
Persona: Lead Tech

Erreur: IntegrityError - duplicate key value violates unique constraint "products_sku_key"

Stack trace:
sqlalchemy.exc.IntegrityError: (asyncpg.exceptions.UniqueViolationError)
duplicate key value violates unique constraint "products_sku_key"

Code:
product = Product(sku="TEST-001", title="Test")
await db.add(product)
await db.commit()

Attendu: Produit créé
Actuel: Erreur

Question: Cause et fix.
```

---

### ⚡ Optimiser Performance

```
Persona: DevOps Engineer

Contexte: [ENDPOINT/FONCTION] est lent.

Performance actuelle: [X]ms (objectif < [Y]ms)

Profiling:
- [Partie 1]: [X]% du temps
- [Partie 2]: [Y]% du temps

Code:
[CODE]

Question:
1. Identifie le bottleneck principal
2. Propose 2-3 optimizations concrètes
3. Estimation de gain pour chaque optimization

Contraintes:
- Pas de changement de stack
- Backward compatible
```

**Exemple concret :**
```
Persona: DevOps Engineer

Endpoint: GET /graphql?query=products

Actuel: 3000ms (objectif < 200ms)

Profiling:
- DB queries: 90% (N+1 problem)
- Python calculs: 10%

Code:
products = await db.execute(select(Product))
for product in products:
    run_rate = await get_run_rate(product.id)

Question: Optimizations.
```

---

## 7. Prompts Documentation

### 📝 Documenter une Fonction

```
Persona: Lead Tech

Contexte: Documenter fonction [NOM_FONCTION].

Code:
[CODE]

Question: Génère docstring Google Style avec:
1. Description claire (1-2 phrases)
2. Args (type + description)
3. Returns (type + description)
4. Raises (exceptions possibles)
5. Example (usage concret)
6. Notes (edge cases, hypothèses)

Contraintes:
- Clair pour développeur junior
- Exemples exécutables
```

**Exemple concret :**
```
Persona: Lead Tech

Fonction:
def calculate_stockout_date(stock: int, run_rate: float) -> date | None:
    if run_rate <= 0:
        return None
    days = stock / run_rate
    return date.today() + timedelta(days=int(days))

Question: Docstring complète.
```

---

### 📚 Créer README Module

```
Persona: Lead Tech

Contexte: Créer README.md pour module [NOM_MODULE].

Module contient:
- [Fichier 1]: [Description]
- [Fichier 2]: [Description]

Question: Génère README.md avec:
1. Overview (qu'est-ce que ce module fait)
2. Structure fichiers
3. Usage (exemples de code)
4. Tests (comment lancer)
5. Architecture (diagramme ASCII si pertinent)

Format: Markdown
```

**Exemple concret :**
```
Persona: Lead Tech

Module: forecasting/

Contient:
- algorithms/out_of_stock_correction.py
- algorithms/outlier_detection.py
- service.py

Question: README.md module forecasting.
```

---

## 🎯 Templates Rapides (Copy-Paste)

### Démarrer Epic N

```
Persona: Scrum Master

Sprint [N] - Epic [X]
Objectif: [DESCRIPTION]

User Stories:
[LISTE US avec story points]

Question: Plan de sprint complet (tâches, estimation, risques).
```

### Implémenter US X.Y

```
Persona: Lead Tech

US [X.Y]: [DESCRIPTION]

Critères acceptation:
[LISTE CRITÈRES]

Question: Implémentation complète (backend + frontend + tests).
```

### Fix Bug

```
Persona: Lead Tech

Bug: [DESCRIPTION]
Reproduction: [STEPS]
Erreur: [MESSAGE]

Question: Cause root + fix.
```

### Review Sécurité

```
Persona: Security Engineer

Code review: [MODULE/ENDPOINT]
Question: Audit OWASP + fixes.
```

---

## 📋 Checklist Utilisation Prompts

Avant d'envoyer un prompt :

- [ ] **Persona défini** (quel expert consulter ?)
- [ ] **Contexte clair** (problème, contraintes)
- [ ] **Code/données fournis** (si pertinent)
- [ ] **Question précise** (objectif clair)
- [ ] **Critères de succès** (comment valider ?)

---

**Ces templates accélèrent le développement avec Claude Code ! 道💜**

**Pour aller plus loin :** Voir [claude.md](claude.md) pour détails sur chaque persona.
