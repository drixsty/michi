# Guide d'inscription — Connecteur eBay

**Plateforme :** eBay REST APIs (Sell Inventory, Sell Analytics, Sell Fulfillment)  
**Durée estimée :** 1–2 jours (revue eBay pour scopes sensibles)  
**Prérequis :** Compte eBay vendeur actif + compte eBay Developer Program (gratuit)

---

## Table des Matières

1. [Vue d'ensemble eBay APIs](#1-vue-densemble-ebay-apis)
2. [Créer un compte eBay Developer](#2-créer-un-compte-ebay-developer)
3. [Créer l'application eBay](#3-créer-lapplication-ebay)
4. [Configurer les scopes OAuth](#4-configurer-les-scopes-oauth)
5. [Générer le Refresh Token vendeur](#5-générer-le-refresh-token-vendeur)
6. [Configurer les variables d'environnement](#6-configurer-les-variables-denvironnement)
7. [Stocker les credentials dans Michi](#7-stocker-les-credentials-dans-michi)
8. [Marketplaces eBay supportées](#8-marketplaces-ebay-supportées)
9. [Gestion de l'expiration du Refresh Token](#9-gestion-de-lexpiration-du-refresh-token)
10. [Passer en production](#10-passer-en-production)
11. [Vérification & dépannage](#11-vérification--dépannage)

---

## 1. Vue d'ensemble eBay APIs

Michi utilise trois APIs eBay REST :

| API | Endpoint | Usage Michi |
|---|---|---|
| **Sell Inventory API v1** | `/sell/inventory/v1/inventory_item` | Catalogue produits + stock |
| **Sell Fulfillment API v1** | `/sell/fulfillment/v1/order` | Historique commandes filtrées par SKU |
| **Sell Account API v1** | `/sell/account/v1/privilege` | Validation des credentials |

### Authentification OAuth 2.0

eBay utilise un flux **Authorization Code** standard. Le `refresh_token` obtenu dure **18 mois** (renouvelable).

```
Client Credentials (App ID + Cert ID)
        │
        ▼
POST https://api.ebay.com/identity/v1/oauth2/token
  Authorization: Basic {base64(app_id:cert_id)}
  grant_type=refresh_token
  &refresh_token={vendeur_refresh_token}
  &scope={scopes}
        │
        ▼
{"access_token": "v^1.1#i^1...", "expires_in": 7200}
```

---

## 2. Créer un compte eBay Developer

1. Aller sur **https://developer.ebay.com**
2. Cliquer **"Join"** (en haut à droite)
3. Se connecter avec votre compte eBay existant (ou créer un compte)
4. Accepter les **eBay Developer Program Agreement**
5. Accéder au **Developer Hub** → **My Account**

> Le Developer Program est **gratuit** pour les vendeurs.

---

## 3. Créer l'application eBay

### 3.1 Générer les Application Keys

1. **Developer Hub** → **My Account** → **Application Keys**
2. Cliquer **"Create a Keyset"**
3. Choisir **"Production"** (pas Sandbox pour Michi)
4. Remplir :

| Champ | Valeur |
|---|---|
| Application title | `Michi Inventory Forecasting` |
| Application category | `Selling tools` |
| Primary marketplace | `eBay France (EBAY_FR)` |

5. Cliquer **"Create"**

### 3.2 Credentials générés

Vous obtenez 3 clés pour l'environnement Production :

| Credential | Nom interne eBay | Description |
|---|---|---|
| **App ID** | `Client ID` | Identifiant public de l'application |
| **Cert ID** | `Client Secret` | Secret de l'application |
| **Dev ID** | `Dev ID` | Identifiant du développeur (rarement utilisé) |

> Conserver `App ID` et `Cert ID` — ils forment la paire `client_id:client_secret` pour l'authentification Basic.

---

## 4. Configurer les scopes OAuth

### Scopes requis pour Michi

| Scope | Usage |
|---|---|
| `https://api.ebay.com/oauth/api_scope/sell.inventory` | Lire les listings et stocks |
| `https://api.ebay.com/oauth/api_scope/sell.analytics.readonly` | Métriques de trafic |
| `https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly` | Commandes complétées |

### Activer les scopes dans le Developer Hub

1. **My Account** → **Application Keys** → cliquer sur votre application
2. Onglet **"OAuth"** → section **"User Access Token"**
3. Cliquer **"Add OAuth Scope"**
4. Ajouter les 3 scopes listés ci-dessus
5. Sauvegarder

> Certains scopes nécessitent une **revue eBay** (1–2 jours). `sell.inventory` est généralement approuvé automatiquement pour les vendeurs actifs.

---

## 5. Générer le Refresh Token vendeur

Le `refresh_token` autorise votre application à accéder au compte du vendeur.

### 5.1 URL d'autorisation

Construire l'URL OAuth et la partager avec le vendeur :

```
https://auth.ebay.com/oauth2/authorize
  ?client_id={YOUR_APP_ID}
  &response_type=code
  &redirect_uri={YOUR_RU_NAME}
  &scope=https://api.ebay.com/oauth/api_scope/sell.inventory
         https://api.ebay.com/oauth/api_scope/sell.analytics.readonly
         https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly
  &state={random_nonce}
```

> **RuName (Redirect URI Name)** : eBay utilise un alias pour les URLs de redirection. Créer le RuName dans le Developer Hub → votre app → onglet **"OAuth"** → **"User Tokens"** → **"Add eBay Redirect URL"**.

### 5.2 Créer le RuName

1. **Developer Hub** → votre app → **"User Tokens"**
2. Cliquer **"Add eBay Redirect URL"**
3. Configurer :

| Champ | Valeur |
|---|---|
| Display Title | `Michi Production Redirect` |
| Privacy Policy URL | `https://michi.app/privacy` |
| Your Auth Accepted URL | `https://api.michi.app/ebay/callback` |
| Your Auth Declined URL | `https://michi.app/connect?error=ebay_declined` |

4. Sauvegarder → eBay génère le **RuName** (ex: `KevinTSAGUE-MichiInv-PRD-xxxxx`)

### 5.3 Callback & échange du code

eBay redirige vers votre callback avec :

```
GET https://api.michi.app/ebay/callback
  ?code={authorization_code}
  &state={nonce}
  &expires_in=299
```

Échange du code :

```bash
curl -X POST https://api.ebay.com/identity/v1/oauth2/token \
  -H "Authorization: Basic $(echo -n '{APP_ID}:{CERT_ID}' | base64)" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code={authorization_code}" \
  -d "redirect_uri={RuName}"
```

Réponse :

```json
{
  "access_token": "v^1.1#i^1#f^0#p^3...",
  "token_type": "User Access Token",
  "expires_in": 7200,
  "refresh_token": "v^1.1#i^1#f^1#r^1...",
  "refresh_token_expires_in": 47304000
}
```

> `refresh_token_expires_in` = 47 304 000 secondes = **18 mois**. Stocker la date d'expiration pour alerter le vendeur avant.

---

## 6. Configurer les variables d'environnement

```bash
# apps/api/.env.production
USE_MOCK_EBAY=false

# Clé de chiffrement globale (partagée avec Amazon, Etsy)
ENCRYPTION_KEY=your_32_bytes_base64_key
```

---

## 7. Stocker les credentials dans Michi

```python
from core.security.encryption import encrypt_field
from datetime import datetime, timedelta

# Calculer la date d'expiration du refresh token (18 mois)
refresh_expires_at = datetime.utcnow() + timedelta(seconds=refresh_token_expires_in)

await session.execute(
    insert(StoreCredential).values(
        store_id=store.id,
        encrypted_access_token=encrypt_field(refresh_token),    # v^1.1#i^1#f^1...
        encrypted_api_key=encrypt_field(app_id),                # App ID eBay
        encrypted_api_secret=encrypt_field(cert_id),            # Cert ID eBay
        meta={
            "marketplace_id": "EBAY_FR",
            "refresh_token_expires_at": refresh_expires_at.isoformat(),
            "ru_name": ru_name,
        }
    )
)
```

### Passage au connecteur

```python
credentials = {
    "ebay_client_id":     decrypt_field(cred.encrypted_api_key),
    "ebay_client_secret": decrypt_field(cred.encrypted_api_secret),
    "ebay_refresh_token": decrypt_field(cred.encrypted_access_token),
    "marketplace_id":     cred.meta.get("marketplace_id", "EBAY_FR"),
}

await ebay_connector.fetch_all_data(shop_id, credentials=credentials)
```

---

## 8. Marketplaces eBay supportées

| Pays | marketplace_id | Notes |
|---|---|---|
| France | `EBAY_FR` | Plateforme principale Michi |
| Allemagne | `EBAY_DE` | Plus grande marketplace eBay EU |
| Royaume-Uni | `EBAY_GB` | Post-Brexit : douanes UK |
| Italie | `EBAY_IT` | |
| Espagne | `EBAY_ES` | |
| Pays-Bas | `EBAY_NL` | |
| Belgique | `EBAY_BE` | |
| Pologne | `EBAY_PL` | |
| Autriche | `EBAY_AT` | |
| Suisse | `EBAY_CH` | Hors UE (TVA spécifique) |
| États-Unis | `EBAY_US` | Requiert sandbox séparé pour les tests |

> Michi cible les marchands EU — `EBAY_FR` est la valeur par défaut dans le connecteur.

---

## 9. Gestion de l'expiration du Refresh Token

Le refresh token eBay expire après **18 mois** — contrairement à Amazon et Shopify. Un mécanisme de renouvellement est nécessaire.

### Plan de renouvellement recommandé

```
J-30 avant expiration :
  → Notification email au marchand (depuis Michi Alerts)
  → Bannière UI dans le dashboard (ConnectorStatus = "expiring_soon")

J-7 avant expiration :
  → Notification urgente + bouton "Renouveler"
  → ConnectorStatus = "expiring_critical"

J+0 (expiration) :
  → ConnectorStatus = "disconnected"
  → Ingestion eBay suspendue, données freezées
  → Email de reconnexion obligatoire
```

### Vérification de la date d'expiration

```python
from datetime import datetime

expires_at_str = store_cred.meta.get("refresh_token_expires_at")
if expires_at_str:
    expires_at = datetime.fromisoformat(expires_at_str)
    days_remaining = (expires_at - datetime.utcnow()).days
    
    if days_remaining < 30:
        # Déclencher alerte dans le système Michi
        await alert_service.create_alert(
            type="CONNECTOR_EXPIRING",
            message=f"Token eBay expire dans {days_remaining} jours",
            severity=2 if days_remaining < 7 else 1
        )
```

---

## 10. Passer en production

### Checklist avant activation

- [ ] `USE_MOCK_EBAY=false` dans `.env.production`
- [ ] App ID + Cert ID configurés dans StoreCredential
- [ ] RuName créé et URL callback HTTPS enregistrée
- [ ] Scopes `sell.inventory`, `sell.analytics.readonly`, `sell.fulfillment.readonly` approuvés
- [ ] Refresh token obtenu via le flux OAuth complet
- [ ] Date d'expiration du refresh token stockée dans `meta`
- [ ] Job de monitoring d'expiration configuré
- [ ] `ENCRYPTION_KEY` configuré

### Limites API eBay (production)

| API | Limite quotidienne | Requêtes/seconde |
|---|---|---|
| Sell Inventory API | 1 000 000 | 5 |
| Sell Fulfillment API | 500 000 | 5 |
| Sell Analytics API | 250 000 | 2 |

---

## 11. Vérification & dépannage

### Test de connexion

```bash
# 1. Obtenir un access token
curl -X POST https://api.ebay.com/identity/v1/oauth2/token \
  -H "Authorization: Basic $(echo -n 'APP_ID:CERT_ID' | base64)" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&refresh_token=v^1.1#i^1...&scope=https://api.ebay.com/oauth/api_scope/sell.inventory"

# 2. Tester l'API Inventory
curl -H "Authorization: Bearer {ACCESS_TOKEN}" \
     -H "X-EBAY-C-MARKETPLACE-ID: EBAY_FR" \
     "https://api.ebay.com/sell/inventory/v1/inventory_item?limit=5"
```

### Erreurs courantes

| Code HTTP | Message eBay | Cause | Solution |
|---|---|---|---|
| `401` | `Invalid access token` | Token expiré (2h) | Rafraîchir le token (automatique dans le connecteur) |
| `401` | `Invalid refresh token` | Refresh token révoqué ou expiré (18 mois) | Refaire le flux OAuth complet |
| `403` | `Insufficient permissions` | Scope non accordé | Ajouter le scope dans Developer Hub |
| `429` | `Request limit exceeded` | Rate limit dépassé | Respecter les 5 req/s, utiliser `@retry` |
| `404` | `Inventory item not found` | SKU inexistant | Vérifier que le listing est actif |
| `503` | `Service temporarily unavailable` | Maintenance eBay | Attendre, le `@retry(3)` gère automatiquement |

### Logs à surveiller

```python
# ebay.py
logger.debug(f"[eBay] Token rafraîchi pour client_id={cache_key[:8]}...")
logger.info(f"[eBay] fetch_products : {len(products)} listings récupérés")
logger.info(f"[eBay] fetch_sales_history : {len(sales)} jours pour SKU={product_sku}")
logger.error(f"[eBay] validate_connection échoué : {exc}")
```

---

*Retour : [connectors.md](connectors.md)*
