---
id: sprint-21
title: Sprint 21 — DDD Hexagonal
sidebar_label: Sprint 21
slug: /sprints/sprint-21
---

# Sprint 21 — DDD Hexagonal + Monorepo + Typage + Tests + Docs + i18n

**Vélocité planifiée :** 111 story points  
**Durée :** 4 semaines (Sprint 21A + Sprint 21B)

## Avancement

| Epic | US | SP | Statut |
|------|----|----|--------|
| G — Module `intelligence/` | US 21.30 | 8 | ✅ |
| B — DDD Auth Domain | US 21.6 | 5 | ✅ |
| B — DDD Auth Infrastructure | US 21.7 | 5 | ✅ |
| B — DDD Auth Application | US 21.8 | 5 | ✅ |
| B — Fix OAuth async | US 21.13 | 2 | ✅ |
| C — mypy strict | US 21.14 | 5 | ✅ |
| D — Docusaurus setup | US 21.17 | 5 | ✅ |

## Livrables Sprint 21A

### Module `intelligence/` (US 21.30 — P0)

Bounded context IA zero-dependency :
- 6 algorithmes migrés depuis `forecasting/algorithms/`
- 3 fonctions analytics extraites de `decisions/service.py`
- Pipeline OOS → IQR → RunRate sans DB
- Domain : entités + ports Protocol
- 28 tests, 100% pass, couverture 76%

### Architecture DDD Auth (US 21.6 / 21.7 / 21.8)

- **Domain** : `UserEntity`, `OrgSlug`, `Email`, `HashedPassword`, ports Protocol
- **Infrastructure** : 4 repositories SQLAlchemy, mappers, `BCryptPasswordHasher`
- **Application** : `ApplicationAuthService`, `ApplicationOrgService`, `build_auth_service()`
- Factory pattern pour injection de dépendances

### Typage strict (US 21.14)

```bash
# 0 erreur sur intelligence/ + auth/domain/
mypy src/modules/intelligence/ src/modules/auth/domain/ --strict
# Success: no issues found in 26 source files
```

`pyproject.toml` configuré avec `strict = true` + overrides ciblés pour SQLAlchemy legacy.

## Règle DDD Rule 6 — Vérifiée

```bash
grep -r "import sqlalchemy" backend/src/modules/intelligence/
# → 0 résultat ✅
```
