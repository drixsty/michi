---
id: graphql
title: API GraphQL Reference
sidebar_label: 🔌 GraphQL
---

# API GraphQL Reference

Michi 道 utilise une API GraphQL robuste reposant sur **Strawberry GraphQL** (Python) et **Apollo Client** (TypeScript).

## 🚀 Accès à l'API

- **Endpoint :** `http://localhost:8000/graphql`
- **Playground :** Accédez directement à l'URL ci-dessus dans votre navigateur pour tester les requêtes.

## 📜 Schéma SDL

Le schéma complet est exporté dans le monorepo sous `packages/types/schema.graphql`.

### Échantillon des Queries Principales

#### `me: UserType!`
Récupère les informations de l'utilisateur connecté via son JWT.

#### `dashboardKpis(storeId: ID): DashboardKPIType!`
Retourne les indicateurs de performance clés (KPIs) pour le tableau de bord omnicanal.

#### `omnichannelInventory: [OmnichannelProductType!]!`
Récupère la liste consolidée des produits sur tous les canaux configurés (Shopify, Amazon, etc.).

## 📦 Typage Frontend (Codegen)

Nous utilisons `@graphql-codegen` pour synchroniser automatiquement les types Backend avec le Frontend.

### Utilisation :
1. Modifiez votre query dans `/apps/web/src/graphql/`.
2. Exécutez `npm run codegen` dans la racine ou `packages/types`.
3. Importez les types générés :

```typescript
import { GetProductsQuery } from '@michi/types';

const { data } = useQuery<GetProductsQuery>(GET_PRODUCTS);
```

### Commandes utiles :
- `make schema` : Exporte le schéma SDL du backend.
- `npm run codegen` : Génère les types TypeScript.

---

:::tip Sécurité
Toutes les requêtes (sauf login/register) nécessitent un header d'Authorization :
`Authorization: Bearer <votre_token_jwt>`
:::
