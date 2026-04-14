---
id: auth-flow
title: Flux authentification JWT
sidebar_label: Auth Flow
slug: /architecture/auth-flow
---

# Flux Authentification JWT

## Login classique

```
Client → POST /graphql (mutation login)
    │
    ▼ Resolver (thin) → build_auth_service(db)
    │
    ▼ ApplicationAuthService.login(email, password)
    │
    ├─▶ SQLAlchemyUserRepository.get_model_by_email()
    ├─▶ BCryptPasswordHasher.verify()
    └─▶ JwtTokenService.create_access_token()
    │
    ▼ AuthPayload { token, user }
```

## Google OAuth

```
Client → POST /graphql (mutation googleLogin)
    │
    ▼ Resolver → await httpx.AsyncClient.get(tokeninfo)
    │
    ▼ ApplicationAuthService.login_with_google(google_id, email)
    │
    ├─▶ Cherche user par email ou google_id
    ├─▶ Si absent → crée User + Organization + Membership (ADMIN)
    ├─▶ Si Stripe activé → billing.create_customer()
    └─▶ JwtTokenService.create_access_token()
```

## Token JWT

```json
{
  "user_id": "uuid",
  "org_id": "uuid | null",
  "email": "user@example.com",
  "exp": 1234567890
}
```

Expiration : **24h** (configurable via `ACCESS_TOKEN_EXPIRE_HOURS`).

## RBAC — Rôles

| Rôle | Droits |
|------|--------|
| `ADMIN` | Tous les droits |
| `MANAGER` | Lecture + écriture produits/commandes |
| `VIEWER` | Lecture seule |

Les droits granulaires sont stockés dans `organization_members.permissions` (JSONB).
