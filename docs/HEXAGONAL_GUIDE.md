# Guide de Développement : Architecture Hexagonale (Michi 道)

Ce guide explique comment ajouter une nouvelle fonctionnalité au backend (`apps/api`) en respectant les principes de l'architecture hexagonale (Ports & Adapters) et du DDD.

---

## 🏗️ Les 3 Couches du Module

Chaque module métier (ex: `inventory`, `auth`) doit être divisé en trois sous-dossiers :

### 1. Domain (`domain/`)
**Rôle** : Le cœur du métier. Contient la logique pure, les entités et les contrats.
- **Entities** : Classes Pydantic ou Dataclasses représentant les objets métier (ex: `ProductEntity`).
- **Enums** : Source de vérité unique pour les énumérations (ex: `PlatformSource`).
- **Ports (Interfaces)** : Définition des interfaces de dépôts ou de services externes (ex: `IProductRepository`).

> [!IMPORTANT]
> Cette couche ne doit avoir **aucune dépendance** vers l'extérieur (pas de SQLAlchemy, pas de FastAPI).

### 2. Application (`application/`)
**Rôle** : Orchestration des cas d'utilisation (Use Cases).
- **Services** : Classes qui manipulent les entités via les ports (ex: `ProductService`).
- **Logique** : Calculs complexes, validations métier multi-domaines.

> [!TIP]
> Injectez toujours les repositories via leurs interfaces (`Ports`) dans le constructeur pour faciliter le test avec des **Fakes**.

### 3. Infrastructure (`infrastructure/`)
**Rôle** : Implémentations concrètes et adaptateurs.
- **Persistence** : Modèles SQLAlchemy et implémentations des repositories (ex: `SQLAlchemyProductRepository`).
- **Adapters** : Clients API (Shopify), Envoi d'emails, Clients Redis.
- **Mapping** : Conversion entre Modèles DB et Entités Domain.

---

## 🏃 Workflow : Ajouter une Feature

### Étape 1 : Définir l'Entité (Domain)
Créez ou modifiez `domain/entities.py`.
```python
class MyFeatureEntity(BaseModel):
    id: UUID
    name: str
```

### Étape 2 : Définir le Port (Domain)
Créez ou modifiez `domain/ports.py`.
```python
class IMyFeatureRepository(ABC):
    @abstractmethod
    async def save(self, entity: MyFeatureEntity) -> None:
        pass
```

### Étape 3 : Implémenter le Service (Application)
Créez `application/service.py`.
```python
class MyFeatureService:
    def __init__(self, repo: IMyFeatureRepository):
        self.repo = repo
```

### Étape 4 : Implémenter le Repository (Infrastructure)
Créez le modèle SQLAlchemy dans `infrastructure/persistence/models.py` et le dépôt dans `infrastructure/repositories/`.

### Étape 5 : Exposer via GraphQL
Ajoutez les resolvers dans `src/modules/myscope/adapters/resolvers.py` (ou directement dans `src/core/graphql/` selon le scope).

---

## 🧪 Stratégie de Test

1. **Unit Tests** : Testez les services `application/` en injectant des `FakeRepositories`.
2. **Integration Tests** : Testez les `infrastructure/repositories/` avec une base de données SQLite in-memory.
3. **E2E Tests** : Testez les mutations GraphQL complètes.

> [!CAUTION]
> N'utilisez jamais d'objets SQLAlchemy dans la couche Application ou Domain. Tout passage de donnée doit se faire via des **Entités**.
