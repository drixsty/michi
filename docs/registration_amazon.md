# Guide d'inscription — Connecteur Amazon SP-API

**Plateforme :** Amazon Selling Partner API (SP-API)  
**Durée estimée :** 2–5 jours ouvrés (validation Amazon obligatoire)  
**Prérequis :** Compte Amazon Seller Central actif (EU) + compte développeur Amazon

---

## Table des Matières

1. [Vue d'ensemble SP-API](#1-vue-densemble-sp-api)
2. [Créer le compte développeur Amazon](#2-créer-le-compte-développeur-amazon)
3. [Enregistrer l'application SP-API](#3-enregistrer-lapplication-sp-api)
4. [Demander les rôles (permissions)](#4-demander-les-rôles-permissions)
5. [Obtenir le Refresh Token vendeur (OAuth LWA)](#5-obtenir-le-refresh-token-vendeur-oauth-lwa)
6. [Configurer les variables d'environnement](#6-configurer-les-variables-denvironnement)
7. [Stocker les credentials dans Michi](#7-stocker-les-credentials-dans-michi)
8. [Marketplaces EU supportées](#8-marketplaces-eu-supportées)
9. [Validation Amazon & mise en production](#9-validation-amazon--mise-en-production)
10. [Vérification & dépannage](#10-vérification--dépannage)

---

## 1. Vue d'ensemble SP-API

L'Amazon Selling Partner API (SP-API) remplace l'ancienne MWS API. Elle utilise le protocole **LWA (Login with Amazon)** — une variante d'OAuth 2.0 avec `grant_type=refresh_token`.

### Flux d'authentification LWA

```
Application Michi (client_id + client_secret)
        │
        ▼
POST https://api.amazon.com/auth/o2/token
  {
    "grant_type": "refresh_token",
    "refresh_token": "{vendeur_refresh_token}",
    "client_id": "{lwa_client_id}",
    "client_secret": "{lwa_client_secret}"
  }
        │
        ▼
{"access_token": "Atza|xxx", "expires_in": 3600}
        │
        ▼
Appels SP-API avec header: X-Amz-Access-Token: Atza|xxx
```

---

## 2. Créer le compte développeur Amazon

### 2.1 Accéder à Seller Central

1. Aller sur **https://sellercentral.amazon.fr** (ou `.de`, `.it`, etc.)
2. Se connecter avec le compte vendeur
3. Menu → **Apps & Services** → **Develop Apps**

### 2.2 Accepter les conditions développeur

1. Cliquer **"Register as a developer"**
2. Remplir le formulaire :

| Champ | Valeur |
|---|---|
| Developer name | `Michi - Inventory Forecasting` |
| Developer type | `ISV (Independent Software Vendor)` |
| Primary use case | `Inventory Management` |
| Country | France (ou pays du développeur) |

3. Accepter les **SP-API Developer Agreement**
4. Valider avec un code 2FA (si activé)

---

## 3. Enregistrer l'application SP-API

### 3.1 Créer une nouvelle application

1. **Seller Central** → **Apps & Services** → **Develop Apps**
2. Bouton **"Add new app client"** (ou "Créer une nouvelle application")
3. Remplir les champs :

| Champ | Valeur |
|---|---|
| App name | `Michi Inventory Sync` |
| OAuth redirect URI | `https://api.michi.app/amazon/callback` |
| IAM ARN | *(laisser vide pour les apps vendeur-only)* |

4. Cliquer **"Save and exit"**

### 3.2 Récupérer les credentials LWA

Après enregistrement, Amazon génère :

| Credential | Description | Stockage Michi |
|---|---|---|
| `LWA Client ID` | `amzn1.application-oa2-client.xxx` | `StoreCredential.encrypted_api_key` |
| `LWA Client Secret` | `amzn1.oa2-cs.v1.xxx` | `StoreCredential.encrypted_api_secret` |

> **Important :** Copier le `Client Secret` immédiatement — il ne sera plus affiché en clair après la première visite.

---

## 4. Demander les rôles (permissions)

Les rôles SP-API définissent quelles APIs sont accessibles. Dans la page de votre application :

### Rôles requis pour Michi

| Rôle | Accès | APIs utilisées |
|---|---|---|
| **Catalog Items** | Lecture | `/catalog/2022-04-01/items` — catalogue produits |
| **Sales** | Lecture | `/sales/v1/orderMetrics` — métriques ventes |
| **FBA Inventory** | Lecture | `/fba/inventory/v1/summaries` — stock FBA |

### Rôles optionnels (fonctionnalités futures)

| Rôle | APIs |
|---|---|
| **Orders** | `/orders/v0/orders` — détail commandes |
| **Inventory** | `/fba/inventory/v1` — inventaire MFN |
| **Reports** | `/reports/2021-06-30` — rapports business |

**Comment ajouter les rôles :**

1. Page de l'app → onglet **"Roles"**
2. Cliquer **"Request"** pour chaque rôle
3. Remplir le formulaire de justification :
   - **Use case :** "Synchronize product catalog and sales data for inventory forecasting"
   - **Data usage :** "Read-only access to calculate reorder points and prevent stockouts"
4. Soumettre

> Amazon valide les rôles manuellement — délai moyen **2–3 jours ouvrés** pour un ISV.

---

## 5. Obtenir le Refresh Token vendeur (OAuth LWA)

Le `refresh_token` est unique par compte vendeur. Il autorise votre application à accéder aux données du vendeur.

### 5.1 Flux OAuth LWA (initiation)

L'URL d'autorisation Amazon :

```
https://sellercentral.amazon.fr/apps/authorize/consent
  ?application_id={votre_app_id}
  &state={random_nonce}
  &version=beta
```

> Remplacer `.fr` par le domaine marketplace du vendeur (`.de`, `.it`, etc.)

### 5.2 Callback & échange du code

Amazon redirige vers votre `redirect_uri` avec :

```
GET https://api.michi.app/amazon/callback
  ?spapi_oauth_code={auth_code}
  &state={nonce}
  &selling_partner_id={seller_id}
```

Échange du code contre le refresh_token :

```bash
POST https://api.amazon.com/auth/o2/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code={spapi_oauth_code}
&redirect_uri=https://api.michi.app/amazon/callback
&client_id={lwa_client_id}
&client_secret={lwa_client_secret}
```

Réponse :

```json
{
  "access_token": "Atza|xxx",
  "refresh_token": "Atzr|xxx",
  "token_type": "bearer",
  "expires_in": 3600
}
```

> Le `refresh_token` est **permanent** (sans expiration explicite) — le stocker immédiatement de façon chiffrée.

---

## 6. Configurer les variables d'environnement

```bash
# apps/api/.env.production
USE_MOCK_AMAZON=false

# Note : les credentials LWA sont stockés dans StoreCredential (par boutique),
# pas dans les variables d'environnement globales.
# Seules les clés de chiffrement sont des env vars globaux :
ENCRYPTION_KEY=your_32_bytes_base64_key
```

---

## 7. Stocker les credentials dans Michi

### Schéma de stockage

```python
# Après le callback OAuth Amazon
from core.security.encryption import encrypt_field

await session.execute(
    insert(StoreCredential).values(
        store_id=store.id,
        encrypted_access_token=encrypt_field(refresh_token),    # Atzr|xxx
        encrypted_api_key=encrypt_field(lwa_client_id),         # amzn1.application-oa2-client.xxx
        encrypted_api_secret=encrypt_field(lwa_client_secret),  # amzn1.oa2-cs.v1.xxx
        meta={
            "marketplace_id": "A13V1IB3VIYZZH",  # Amazon.fr
            "seller_id": selling_partner_id,
            "region": "eu-west-1",
        }
    )
)
```

### Passage au connecteur

```python
credentials = {
    "lwa_client_id":     decrypt_field(cred.encrypted_api_key),
    "lwa_client_secret": decrypt_field(cred.encrypted_api_secret),
    "lwa_refresh_token": decrypt_field(cred.encrypted_access_token),
    "marketplace_id":    cred.meta["marketplace_id"],
    "seller_id":         cred.meta.get("seller_id"),
}

await amazon_connector.fetch_all_data(shop_id, credentials=credentials)
```

---

## 8. Marketplaces EU supportées

| Pays | Marketplace ID | Domaine Seller Central |
|---|---|---|
| France | `A13V1IB3VIYZZH` | sellercentral.amazon.fr |
| Allemagne | `A1PA6795UKMFR9` | sellercentral.amazon.de |
| Italie | `APJ6JRA9NG5V4` | sellercentral.amazon.it |
| Espagne | `A1RKKUPIHCS9HS` | sellercentral.amazon.es |
| Royaume-Uni | `A1F83G8C2ARO7P` | sellercentral.amazon.co.uk |
| Pays-Bas | `A1805IZSGTT6HS` | sellercentral.amazon.nl |
| Belgique | `AMEN7PMS3EDWL` | sellercentral.amazon.com.be |
| Pologne | `A1C3SOZRARQ6R3` | sellercentral.amazon.pl |
| Suède | `A2NODRKZP88ZB9` | sellercentral.amazon.se |

### Région API

Tous les marketplaces EU utilisent le endpoint :

```
https://sellingpartnerapi-eu.amazon.com
```

---

## 9. Validation Amazon & mise en production

### Processus de validation SP-API

Amazon impose une revue de sécurité pour passer de l'environnement **sandbox** à la **production**.

#### Étapes de soumission

1. Accéder à **Seller Central** → **Develop Apps** → votre application
2. Onglet **"Authorization"** → cliquer **"Request production access"**
3. Remplir le questionnaire de sécurité :

| Question | Réponse recommandée |
|---|---|
| Data storage | "Données stockées dans PostgreSQL chiffré au repos (AES-256)" |
| Data retention | "Données conservées max 2 ans, suppression sur demande RGPD" |
| Access control | "Authentification JWT + RBAC, accès minimal (lecture seule)" |
| Vulnerability scanning | "Scans OWASP réguliers, pas de données PII dans les logs" |

4. Soumettre et attendre la validation (2–5 jours ouvrés)

#### Environnement sandbox (avant validation)

En attendant la validation, utiliser le **SP-API Sandbox** :

```bash
# Endpoint sandbox (données fictives)
SP_API_BASE=https://sandbox.sellingpartnerapi-eu.amazon.com
```

Les credentials LWA fonctionnent identiquement en sandbox.

### Checklist avant activation production

- [ ] Tous les rôles approuvés par Amazon
- [ ] `USE_MOCK_AMAZON=false` dans `.env.production`
- [ ] Validation Amazon accordée (email de confirmation)
- [ ] URL callback HTTPS enregistrée
- [ ] `ENCRYPTION_KEY` configuré
- [ ] Token LWA rafraîchi dans le cache (TTL 55 min)
- [ ] Monitoring latence SP-API configuré (alerter si > 2s)

---

## 10. Vérification & dépannage

### Test de connexion

```bash
# 1. Obtenir un access token
curl -X POST https://api.amazon.com/auth/o2/token \
  -d "grant_type=refresh_token" \
  -d "refresh_token=Atzr|xxx" \
  -d "client_id=amzn1.application-oa2-client.xxx" \
  -d "client_secret=amzn1.oa2-cs.v1.xxx"

# 2. Tester l'accès catalog
curl -H "x-amz-access-token: Atza|xxx" \
  "https://sellingpartnerapi-eu.amazon.com/catalog/2022-04-01/items?marketplaceIds=A13V1IB3VIYZZH&pageSize=5"
```

### Erreurs courantes

| Code | Message | Cause | Solution |
|---|---|---|---|
| `401` | `InvalidClientTokenId` | `client_id` invalide | Vérifier `lwa_client_id` |
| `401` | `InvalidGrant` | Refresh token révoqué ou expiré | Refaire le flux OAuth LWA |
| `403` | `AccessDenied` | Rôle non accordé ou non validé | Attendre validation Amazon |
| `429` | `QuotaExceeded` | Rate limit dépassé | Réduire la fréquence, augmenter `_RATE_LIMIT_DELAY` |
| `400` | `InvalidInput` | Marketplace ID incorrect | Vérifier la liste des IDs EU |
| `503` | `ServiceUnavailable` | API Amazon en maintenance | Attendre et réessayer (le `@retry` gère ça) |

### Délais de rate limit par endpoint

| Endpoint SP-API | Requests/s | Burst |
|---|---|---|
| `/catalog/2022-04-01/items` | 2 req/s | 2 |
| `/sales/v1/orderMetrics` | 0.5 req/s | 15 |
| `/fba/inventory/v1/summaries` | 2 req/s | 2 |
| `/orders/v0/orders` | 0.0167 req/s | 20 |

---

*Retour : [connectors.md](connectors.md)*
