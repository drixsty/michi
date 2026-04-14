---
id: auth-flow
title: Flux authentification JWT
sidebar_label: Auth Flow
slug: /architecture/auth-flow
---

# Flux Authentification JWT

## Login classique

```mermaid
sequenceDiagram
    participant Client
    participant Resolver as Auth Resolver
    participant Service as AuthService
    participant Repo as UserRepository
    participant Security as JWT & Hashing

    Client->>Resolver: login(email, password)
    Resolver->>Service: login(email, password)
    Service->>Repo: get_by_email()
    Repo-->>Service: UserEntity (hashed_password)
    Service->>Security: verify_password()
    Security-->>Service: Valid ✅
    Service->>Security: create_access_token(user_id, org_id)
    Security-->>Service: token
    Service-->>Resolver: AuthPayload
    Resolver-->>Client: { token, user }
```

## Google OAuth

```mermaid
sequenceDiagram
    participant Client
    participant Resolver as Auth Resolver
    participant Google as Google APIs
    participant Service as AuthService
    participant DB as SQL Database

    Client->>Resolver: googleLogin(idToken)
    Resolver->>Google: verify idToken
    Google-->>Resolver: { email, sub, name }
    Resolver->>Service: login_with_google(email)
    Service->>DB: find or create user/org
    DB-->>Service: Success
    Service-->>Resolver: AuthPayload (Token JWT Michi)
    Resolver-->>Client: { token, user }
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
