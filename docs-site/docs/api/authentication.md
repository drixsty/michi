---
id: authentication
title: API — Authentification
sidebar_label: Authentification
slug: /api/authentication
---

# Authentification

## Mutations

### `login`

```graphql
mutation {
  login(input: { email: "user@example.com", password: "secret" }) {
    token
    user { id email firstName lastName currentOrganizationId }
  }
}
```

### `register`

```graphql
mutation {
  register(input: {
    email: "new@example.com"
    password: "secret"
    firstName: "Alice"
    lastName: "Dupont"
  }) {
    token
    user { id email }
  }
}
```

### `googleLogin`

```graphql
mutation {
  googleLogin(input: { idToken: "<google_id_token>" }) {
    token
    user { id email }
  }
}
```

### `createOrganization`

```graphql
mutation {
  createOrganization(name: "Ma Boutique", plan: "PRO") {
    token
    user { currentOrganizationId }
  }
}
```

### `switchOrganization`

```graphql
mutation {
  switchOrganization(organizationId: "<org_uuid>") {
    token
  }
}
```

## Erreurs courantes

| Code | Message | Cause |
|------|---------|-------|
| `UNAUTHENTICATED` | Invalid email or password | Mauvais credentials |
| `ALREADY_MEMBER` | Email déjà utilisé | Register avec email existant |
| `INVITATION_ALREADY_PENDING` | Invitation déjà en attente | Double invitation |
