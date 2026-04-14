---
id: ddd-hexagonal
title: DDD & Architecture Hexagonale
sidebar_label: 🧱 DDD & Hexagonale
sidebar_position: 2
---

# Domain-Driven Design & Architecture Hexagonale

Michi 道 applique une architecture hexagonale (Ports & Adapteurs) pour isoler le cœur métier des détails techniques (base de données, APIs externes).

## 🏙️ Structure des Modules

Chaque module (auth, inventory, forecasting, etc.) suit cette structure interne :

```text
src/modules/[module_name]/
├── domain/              # Port (Entities, Value Objects, Repository Interfaces)
│   ├── entities.py
│   └── repository.py    # Interface abstraite
├── application/         # Orchestration (Services)
│   └── service.py       # Logique métier pure
├── infrastructure/      # Adapter (Persistence, External APIs)
│   └── repositories/
│       └── sqlalchemy.py # Implémentation réelle
└── adapters/            # Adapter (GraphQL, CLI)
    └── resolvers.py    # Point d'entrée GraphQL
```

```mermaid
sequenceDiagram
    participant Adapter as Adapter (GraphQL/CLI)
    participant Service as Application (Service)
    participant Port as Port (Protocol Interface)
    participant Repo as Infrastructure (Repository)
    participant DB as SQL Database

    Adapter->>Service: Appel de la méthode métier
    Service->>Port: Appel de l'interface Domain (Repo)
    Port-->>Repo: Implémentation via DI
    Repo->>DB: Requête SQLAlchemy
    DB-->>Repo: Données SQL
    Repo-->>Service: Entités Domain
    Service-->>Adapter: Résultat métier typé
```

## 🔌 Ports et Adapteurs

### Le Port (Domain)
C'est l'interface définie par le domaine pour interagir avec le monde extérieur.
Exemple : `IProductRepository` définit que l'on doit pouvoir "récupérer un produit", mais ne sait pas comment.

### L'Adapteur (Infrastructure)
C'est l'implémentation concrète.
Exemple : `SQLAlchemyProductRepository` utilise la session DB pour exécuter du SQL.

## ⚖️ Avantages
1. **Testabilité :** On peut tester les services avec des "FakeRepositories" (en mémoire) sans base de donnée.
2. **Maintenance :** Changer de base de données ou de framework API n'impacte pas la logique métier.
3. **Clarté :** La séparation des responsabilités est explicite.
