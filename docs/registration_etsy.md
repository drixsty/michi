# Guide d'inscription — Connecteur Etsy

**Plateforme :** Etsy Open API v3  
**Durée estimée :** 30 minutes (approbation quasi-immédiate)  
**Prérequis :** Compte Etsy vendeur actif avec une boutique ouverte

---

## Table des Matières

1. [Vue d'ensemble Etsy API v3](#1-vue-densemble-etsy-api-v3)
2. [Créer une application Etsy](#2-créer-une-application-etsy)
3. [Configurer les scopes OAuth](#3-configurer-les-scopes-oauth)
4. [Implémenter le flux OAuth PKCE](#4-implémenter-le-flux-oauth-pkce)
5. [Récupérer le Shop ID](#5-récupérer-le-shop-id)
6. [Configurer les variables d'environnement](#6-configurer-les-variables-denvironnement)
7. [Stocker les credentials dans Michi](#7-stocker-les-credentials-dans-michi)
8. [Particularités Etsy : variantes & SKUs](#8-particularités-etsy--variantes--skus)
9. [Gestion de l'expiration du Refresh Token (90 jours)](#9-gestion-de-lexpiration-du-refresh-token-90-jours)
10. [Passer en production](#10-passer-en-production)
11. [Vérification & dépannage](#11-vérification--dépannage)

---

## 1. Vue d'ensemble Etsy API v3

L'Etsy Open API v3 utilise **OAuth 2.0 avec PKCE** (Proof Key for Code Exchange) — une sécurité supplémentaire qui ne nécessite pas de stocker le `client_secret` côté serveur.

### APIs utilisées par Michi

| Endpoint | Usage |
|---|---|
| `GET /v3/application/shops/{shop_id}` | Validation connection |
| `GET /v3/application/shops/{shop_id}/listings/active` | Catalogue produits + variantes |
| `GET /v3/application/listings/{listing_id}/inventory` | Stock par variante |
| `GET /v3/application/shops/{shop_id}/receipts` | Commandes complétées → ventes |

### Spécificités Etsy

- **Listings** = produits, avec potentiellement N variantes (taille, couleur)
- **Receipts** = commandes client (≠ line items individuels)
- **Transactions** = lignes de commande à l'intérieur d'un Receipt
- Le **SKU** peut être vide sur les anciennes boutiques → Michi utilise le `listing_id` comme fallback

---

## 2. Créer une application Etsy

### 2.1 Accéder à la page développeurs

1. Aller sur **https://www.etsy.com/developers**
2. Se connecter avec votre compte Etsy (celui du vendeur ou un compte séparé)
3. Cliquer **"Register a new app"**

### 2.2 Remplir le formulaire de création

| Champ | Valeur | Notes |
|---|---|---|
| **Application name** | `Michi Inventory Sync` | Visible par les marchands lors de l'auth |
| **Application website** | `https://michi.app` | URL de votre site SaaS |
| **Description** | `Synchronisation inventaire e-commerce pour prévision de réapprovisionnement` | Description claire de l'usage |
| **Primary use** | `Sell products or services` → `Inventory management` | Sélectionner la catégorie la plus proche |
| **Redirect URI** | `https://api.michi.app/etsy/callback` | URL callback OAuth |

### 2.3 Récupérer le Keystring

Après soumission, Etsy génère immédiatement un **Keystring** (= `client_id` dans la terminologie OAuth) :

```
Keystring : xxxxxxxxxxxxxxxxxxxxxxxx
```

> Etsy API v3 avec PKCE **ne nécessite pas de client_secret**. Le Keystring seul suffit.

---

## 3. Configurer les scopes OAuth

Etsy v3 utilise des **scopes granulaires**. Les sélectionner lors de la création de l'app ou dans la page de configuration.

### Scopes requis pour Michi

| Scope | Permission | Usage |
|---|---|---|
| `listings_r` | Lecture des listings | Catalogue produits, prix, variantes |
| `transactions_r` | Lecture des transactions | Commandes → calcul ventes/jour |
| `shops_r` | Lecture profil boutique | Validation connection, nom de la boutique |

### Scopes optionnels (fonctionnalités futures)

| Scope | Usage potentiel |
|---|---|
| `listings_w` | Mise à jour stock depuis Michi |
| `profile_r` | Infos profil vendeur |
| `billing_r` | Statistiques facturation |

**Comment configurer :**

1. **https://www.etsy.com/developers** → votre application
2. Section **"Permissions"** → cocher les scopes requis
3. Sauvegarder

---

## 4. Implémenter le flux OAuth PKCE

Le PKCE (Proof Key for Code Exchange) remplace le `client_secret` par un challenge cryptographique généré côté client.

### 4.1 Étape 1 — Générer le PKCE challenge

```python
import secrets
import hashlib
import base64

# Générer le code_verifier (random 43-128 chars)
code_verifier = secrets.token_urlsafe(96)  # ~128 chars

# Calculer le code_challenge = BASE64URL(SHA256(code_verifier))
digest = hashlib.sha256(code_verifier.encode()).digest()
code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
```

### 4.2 Étape 2 — URL d'autorisation

```
https://www.etsy.com/oauth/connect
  ?response_type=code
  &redirect_uri=https://api.michi.app/etsy/callback
  &scope=listings_r+transactions_r+shops_r
  &client_id={etsy_keystring}
  &state={random_nonce}
  &code_challenge={code_challenge}
  &code_challenge_method=S256
```

### 4.3 Étape 3 — Callback

Etsy redirige vers :

```
GET https://api.michi.app/etsy/callback
  ?code={authorization_code}
  &state={nonce}
```

### 4.4 Étape 4 — Échange du code contre les tokens

```bash
curl -X POST https://api.etsy.com/v3/public/oauth/token \
  -H "x-api-key: {etsy_keystring}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id={etsy_keystring}" \
  -d "redirect_uri=https://api.michi.app/etsy/callback" \
  -d "code={authorization_code}" \
  -d "code_verifier={code_verifier}"
```

Réponse :

```json
{
  "access_token": "xxxxxxxxxxxxxxxxxxxxxxxx",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "xxxxxxxxxxxxxxxx"
}
```

> Le `refresh_token` Etsy expire après **90 jours** — bien plus court qu'eBay (18 mois) ou Shopify (permanent).

---

## 5. Récupérer le Shop ID

Le `etsy_shop_id` est nécessaire pour toutes les requêtes API Etsy. Le récupérer après authentification :

```bash
curl -H "Authorization: Bearer {ACCESS_TOKEN}" \
     -H "x-api-key: {etsy_keystring}" \
     "https://openapi.etsy.com/v3/application/users/me/shops"
```

Réponse :

```json
{
  "count": 1,
  "results": [
    {
      "shop_id": 12345678,
      "shop_name": "MaBoutiqueEtsy",
      "currency_code": "EUR",
      "listing_active_count": 47
    }
  ]
}
```

Stocker `shop_id` dans `StoreCredential.meta["etsy_shop_id"]`.

---

## 6. Configurer les variables d'environnement

```bash
# apps/api/.env.production
USE_MOCK_ETSY=false

# Clé de chiffrement (partagée avec Amazon, eBay)
ENCRYPTION_KEY=your_32_bytes_base64_key
```

---

## 7. Stocker les credentials dans Michi

```python
from core.security.encryption import encrypt_field
from datetime import datetime, timedelta

# Le refresh token expire dans 90 jours
refresh_expires_at = datetime.utcnow() + timedelta(days=90)

await session.execute(
    insert(StoreCredential).values(
        store_id=store.id,
        encrypted_access_token=encrypt_field(refresh_token),  # Token 90j
        encrypted_api_key=encrypt_field(etsy_keystring),      # Client ID public
        encrypted_api_secret=None,                            # Pas de secret avec PKCE
        meta={
            "etsy_shop_id": str(shop_id),
            "shop_name": shop_name,
            "refresh_token_expires_at": refresh_expires_at.isoformat(),
        }
    )
)
```

### Passage au connecteur

```python
credentials = {
    "etsy_client_id":     decrypt_field(cred.encrypted_api_key),    # keystring
    "etsy_refresh_token": decrypt_field(cred.encrypted_access_token),
    "etsy_shop_id":       cred.meta["etsy_shop_id"],
}

await etsy_connector.fetch_all_data(shop_id, credentials=credentials)
```

---

## 8. Particularités Etsy : variantes & SKUs

Etsy est la plateforme la plus complexe pour la gestion des SKUs car les produits artisanaux ont souvent des variantes (taille S/M/L, couleur bleu/rouge) sans SKU explicite.

### Stratégie SKU dans le connecteur Michi

```python
# Dans etsy.py — fetch_products()
for variant in products_data:
    # Priorité 1 : SKU explicite configuré par le vendeur
    sku = variant.get("sku")

    # Priorité 2 : Composite listing_id + product_id
    if not sku:
        sku = f"{listing_id}-{variant.get('product_id', '')}"

    # Label lisible : "Robe Bohème — S / Bleu"
    title = f"{listing_title} — {_variant_label(variant)}"
```

### Recommandation pour les marchands Etsy

Encourager les marchands à **configurer des SKUs** sur leurs variantes dans Etsy :

1. Etsy → Gérer la boutique → Listings
2. Éditer un listing → onglet "Variations"
3. Sous chaque variante → champ "SKU" → saisir un code unique (ex: `ROBE-FLEU-S-BLU`)

Sans SKU, Michi utilise `listing_id-product_id` — fonctionnel mais moins lisible dans le dashboard.

---

## 9. Gestion de l'expiration du Refresh Token (90 jours)

Le refresh token Etsy est le plus court-vécu : **90 jours**. Un renouvellement proactif est critique.

### Calendrier de notifications

```
J-14 avant expiration :
  → Email + notification in-app : "Votre connexion Etsy expire bientôt"
  → ConnectorStatus = "expiring_soon" (badge orange dans le dashboard)

J-3 avant expiration :
  → Email urgent + bouton "Reconnecter Etsy maintenant"
  → ConnectorStatus = "expiring_critical" (badge rouge)

J+0 (expiration) :
  → ConnectorStatus = "disconnected"
  → Ingestion Etsy suspendue
  → Alerte critique dans le dashboard Michi

J+7 :
  → Si toujours pas reconnecté : email de relance
  → Données freezées à la dernière sync
```

### Renouvellement automatique si possible

Etsy ne supporte pas le renouvellement automatique "silencieux" : le vendeur doit **re-autoriser manuellement** via le flux OAuth PKCE. L'expérience Michi doit donc :

1. Détecter le J-14 via un job cron quotidien
2. Afficher un CTA dans le dashboard
3. Déclencher le flux OAuth complet lors du clic

```python
# Job cron quotidien (à implémenter dans forecasting/infrastructure/cron_worker.py)
async def check_connector_expiry():
    stores = await store_repo.list_all_with_credentials()
    for store, cred in stores:
        expires_at_str = cred.meta.get("refresh_token_expires_at")
        if not expires_at_str:
            continue
        expires_at = datetime.fromisoformat(expires_at_str)
        days_remaining = (expires_at - datetime.utcnow()).days
        
        if days_remaining <= 14:
            await alert_service.create_alert(
                product_id=None,
                store_id=store.id,
                type="CONNECTOR_EXPIRING",
                message=f"Token {store.platform.value} expire dans {days_remaining} jours",
                severity=2 if days_remaining <= 3 else 1,
            )
```

---

## 10. Passer en production

### Checklist avant activation

- [ ] `USE_MOCK_ETSY=false` dans `.env.production`
- [ ] Keystring configuré dans StoreCredential
- [ ] Scopes `listings_r`, `transactions_r`, `shops_r` activés
- [ ] Flux OAuth PKCE implémenté (`/etsy/callback`)
- [ ] `etsy_shop_id` récupéré et stocké dans `meta`
- [ ] Date d'expiration du refresh token stockée (J+90)
- [ ] Job de monitoring d'expiration configuré
- [ ] `ENCRYPTION_KEY` configuré

### Rate limits Etsy

| Limite | Valeur |
|---|---|
| Requêtes par seconde | 10 req/s |
| Quota journalier par clé | 5 000 req/jour |
| Quota journalier par vendeur | 10 000 req/jour |

> Avec 5 000 req/jour et en paginant à 100 receipts par requête, Michi peut traiter ~500 000 commandes par jour — largement suffisant pour les marchands cibles (50–500 SKU).

---

## 11. Vérification & dépannage

### Test de connexion

```bash
# 1. Rafraîchir le token
curl -X POST https://api.etsy.com/v3/public/oauth/token \
  -H "x-api-key: {etsy_keystring}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&client_id={keystring}&refresh_token={refresh_token}"

# 2. Tester l'accès listings
curl -H "Authorization: Bearer {ACCESS_TOKEN}" \
     -H "x-api-key: {etsy_keystring}" \
     "https://openapi.etsy.com/v3/application/shops/{SHOP_ID}/listings/active?limit=5"
```

### Erreurs courantes

| Code | Message | Cause | Solution |
|---|---|---|---|
| `401` | `Invalid token` | Access token expiré (1h) | Rafraîchir (automatique dans `_get_access_token`) |
| `401` | `Refresh token expired` | Refresh token > 90 jours | Refaire le flux OAuth PKCE complet |
| `403` | `Missing required scope` | Scope non accordé | Ajouter le scope dans la configuration de l'app |
| `404` | `Shop not found` | `etsy_shop_id` incorrect | Vérifier avec `GET /v3/application/users/me/shops` |
| `429` | `Too many requests` | > 10 req/s | `_RATE_LIMIT_DELAY` déjà réglé à 0.12s dans le connecteur |
| `400` | `Invalid code_verifier` | `code_verifier` non stocké correctement en session | Stocker en session Redis entre l'initiation et le callback |

### Logs à surveiller

```python
# etsy.py
logger.debug(f"[Etsy] Token rafraîchi pour client_id={cache_key[:8]}...")
logger.info(f"[Etsy] fetch_products : {len(products)} produits/variantes récupérés")
logger.info(f"[Etsy] fetch_sales_history : {len(sales)} jours pour SKU={product_sku}")
logger.error(f"[Etsy] validate_connection échoué : {exc}")
```

### Tester le flux PKCE en local

Pour tester le flux complet en développement, utiliser `ngrok` pour exposer le callback local :

```bash
# Terminal 1 : démarrer le backend Michi
uvicorn main:app --port 8000

# Terminal 2 : exposer le callback
ngrok http 8000

# Mettre à jour le redirect_uri dans l'app Etsy :
# https://abc123.ngrok.io/etsy/callback
```

---

*Retour : [connectors.md](connectors.md)*
