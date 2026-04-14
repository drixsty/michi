---
id: ddd-hexagonal
title: Architecture DDD Hexagonale
sidebar_label: DDD Hexagonal
slug: /architecture/ddd-hexagonal
---

# Architecture DDD Hexagonale — Sprint 21

## Les 4 couches

```
Domain          → Entités pures + Protocols (aucune dépendance)
Application     → Services métier (reçoivent des Ports par injection)
Infrastructure  → Repositories SQLAlchemy (implémentent les Ports)
Adapters        → Resolvers GraphQL minces (< 15 lignes chacun)
```

## Règles DDD (Charter Sprint 21)

| Règle | Description |
|-------|-------------|
| R1 | Le domaine n'importe jamais SQLAlchemy ni FastAPI |
| R2 | Les services applicatifs reçoivent des ports (Protocol), pas des sessions DB |
| R3 | Les repositories sont la seule couche autorisée à faire du SQL |
| R4 | Les resolvers GraphQL sont minces (< 15 lignes) |
| R5 | Zéro `select()` dans les resolvers |
| R6 | `intelligence/` est zero-dependency (pas de SQLAlchemy, FastAPI, HTTP) |
| R7 | Les imports circulaires sont interdits |

## Structure auth/ (exemple complet)

```
auth/
├── domain/
│   ├── entities.py      # UserEntity, OrgEntity, MembershipEntity
│   ├── value_objects.py # Email, HashedPassword, OrgSlug, JwtToken
│   └── ports.py         # IUserRepository, ITokenService, IOAuthProvider
├── infrastructure/
│   ├── repositories.py  # SQLAlchemyUserRepository (implémente IUserRepository)
│   ├── mappers.py       # SQLAlchemy model ↔ Domain entity
│   └── security_adapters.py  # BCryptPasswordHasher, JwtTokenService
├── application/
│   ├── auth_service.py  # ApplicationAuthService (injecte IUserRepository)
│   ├── org_service.py   # ApplicationOrgService
│   └── factory.py       # build_auth_service(db) → ApplicationAuthService
├── models.py            # SQLAlchemy models (User, Organization, ...)
└── service.py           # Legacy service (à migrer via US 21.9)
```

## Injection de dépendances

```python
# factory.py — point d'entrée unique
from src.modules.auth.application.factory import build_auth_service

auth_svc = build_auth_service(info.context.db, info.context.billing)
result = await auth_svc.login(email, password)
```

Les resolvers n'instancient plus rien directement — ils appellent `build_*`.
