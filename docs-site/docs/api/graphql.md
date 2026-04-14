---
id: graphql
title: API GraphQL — Vue d'ensemble
sidebar_label: GraphQL
slug: /api/graphql
---

# API GraphQL

**Endpoint :** `POST http://localhost:8000/graphql`

Tous les appels passent par un seul endpoint GraphQL (Strawberry + FastAPI).

## Authentification

```http
Authorization: Bearer <jwt_token>
```

Obtenez un token via la mutation `login` ou `googleLogin`.

## Queries principales

```graphql
# Inventaire
query GetInventory($storeId: ID) {
  inventory(storeId: $storeId) {
    products { id sku title currentStock runRate }
    totalCount
  }
}

# Centre décisionnel
query GetDecisions($channel: String) {
  decisionCenter(channel: $channel) {
    kpis {
      inventoryValueCost
      inventoryValueSale
      revenueAtRisk
      stockCoverageAvgDays
      healthScore
    }
    topRisks {
      sku title riskValue daysOfStock stockoutDate
    }
  }
}

# Profil utilisateur
query Me {
  me {
    id email firstName lastName
    organizations { organizationId role }
  }
}
```

## Mutations principales

```graphql
# Auth
mutation Login($email: String!, $password: String!) {
  login(input: { email: $email, password: $password }) {
    token
    user { id email }
  }
}

mutation Register($email: String!, $password: String!, $firstName: String!, $lastName: String!) {
  register(input: { email: $email, password: $password, firstName: $firstName, lastName: $lastName }) {
    token
    user { id email }
  }
}

# Organisation
mutation CreateOrg($name: String!) {
  createOrganization(name: $name) {
    token
    user { currentOrganizationId }
  }
}

mutation SwitchOrg($organizationId: ID!) {
  switchOrganization(organizationId: $organizationId) {
    token
  }
}
```

## Voir aussi

- [Authentification](./authentication)
- [Inventaire](./inventory)
- [Prévisions](./forecasting)
