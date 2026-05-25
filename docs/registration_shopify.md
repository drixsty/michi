# Guide d'inscription — Connecteur Shopify

**Plateforme :** Shopify Admin REST API 2024-01  
**Durée estimée :** 20–30 minutes  
**Prérequis :** Compte Shopify Partners (gratuit) + boutique Shopify active

---

## Table des Matières

1. [Créer un compte Shopify Partners](#1-créer-un-compte-shopify-partners)
2. [Créer l'application Michi](#2-créer-lapplication-michi)
3. [Configurer les scopes OAuth](#3-configurer-les-scopes-oauth)
4. [Configurer les URLs de redirection](#4-configurer-les-urls-de-redirection)
5. [Implémenter le flux OAuth côté Michi](#5-implémenter-le-flux-oauth-côté-michi)
6. [Récupérer l'Access Token permanent](#6-récupérer-laccess-token-permanent)
7. [Stocker les credentials dans Michi](#7-stocker-les-credentials-dans-michi)
8. [Passer en production](#8-passer-en-production)
9. [Vérification & dépannage](#9-vérification--dépannage)

---

## 1. Créer un compte Shopify Partners

1. Aller sur **https://partners.shopify.com**
2. Cliquer **"Join now"** → remplir le formulaire (email, nom de l'organisation)
3. Vérifier l'email de confirmation
4. Se connecter au **Shopify Partners Dashboard**

> Le compte Partners est **gratuit** et permet de créer des applications qui s'installent sur n'importe quelle boutique Shopify.

---

## 2. Créer l'application Michi

Dans le Partners Dashboard :

1. Menu latéral → **Apps**
2. Bouton **"Create app"** en haut à droite
3. Choisir **"Create app manually"**
4. Remplir le formulaire :

| Champ | Valeur |
|---|---|
| App name | `Michi - Inventory Forecasting` |
| App URL | `https://api.michi.app` (ou `http://localhost:8000` en dev) |
| Allowed redirection URL(s) | Voir section 4 |

5. Cliquer **"Create app"**

Vous obtenez automatiquement :
- **API key** (Client ID)
- **API secret key** (Client Secret)

> Conservez ces valeurs — elles sont utilisées dans le flux OAuth.

---

## 3. Configurer les scopes OAuth

Dans la page de votre app → onglet **"Configuration"** → section **"Admin API integration"** :

### Scopes minimum requis pour Michi

| Permission | Accès | Utilisation |
|---|---|---|
| `read_products` | Lecture | Catalogue produits + variantes + stock |
| `read_orders` | Lecture | Historique commandes → calcul ventes/jour |
| `read_inventory` | Lecture | Niveaux de stock multi-location (FBA) |

### Scopes optionnels (fonctionnalités futures)

| Permission | Accès | Utilisation |
|---|---|---|
| `write_inventory` | Écriture | Mise à jour stock depuis Michi |
| `read_fulfillments` | Lecture | Suivi expéditions |
| `read_locations` | Lecture | Entrepôts multiples |

**Comment configurer :**

1. Section "Admin API integration" → cliquer **"Configure"**
2. Cocher les permissions listées ci-dessus
3. Sauvegarder

---

## 4. Configurer les URLs de redirection

Dans la configuration de l'app, section **"App setup"** → **"URLs"** :

| Environnement | App URL | Redirection URL |
|---|---|---|
| Développement | `http://localhost:8000` | `http://localhost:8000/shopify/callback` |
| Staging | `https://api-staging.michi.app` | `https://api-staging.michi.app/shopify/callback` |
| Production | `https://api.michi.app` | `https://api.michi.app/shopify/callback` |

> Shopify autorise plusieurs URLs de redirection. Ajouter les 3 environnements dès maintenant.

---

## 5. Implémenter le flux OAuth côté Michi

Le flux OAuth Shopify est déjà implémenté dans `apps/api/src/modules/shopify/adapters/auth_routes.py`.

### Étape 1 — Initiation (GET /shopify/auth)

```
Marchand clique "Connecter Shopify"
        │
        ▼
GET /shopify/auth?shop=ma-boutique.myshopify.com
        │
        ▼
Redirect vers :
https://ma-boutique.myshopify.com/admin/oauth/authorize
  ?client_id={SHOPIFY_API_KEY}
  &scope=read_products,read_orders,read_inventory
  &redirect_uri=https://api.michi.app/shopify/callback
  &state={random_nonce}
```

### Étape 2 — Callback (GET /shopify/callback)

```
Shopify redirige vers :
GET /shopify/callback
  ?code={auth_code}
  &shop=ma-boutique.myshopify.com
  &state={nonce}
        │
        ▼
POST https://ma-boutique.myshopify.com/admin/oauth/access_token
  {
    "client_id": "{API_KEY}",
    "client_secret": "{API_SECRET}",
    "code": "{auth_code}"
  }
        │
        ▼
Réponse : {"access_token": "shpat_xxx", "scope": "read_products,..."}
        │
        ▼
Stocker access_token chiffré dans StoreCredential
```

### Variables d'environnement backend

```bash
# apps/api/.env
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret_key
SHOPIFY_SCOPES=read_products,read_orders,read_inventory
USE_MOCK_SHOPIFY=false
```

---

## 6. Récupérer l'Access Token permanent

L'`access_token` Shopify est **permanent** (il ne expire pas sauf si le marchand désinstalle l'app ou révoque l'accès).

Après le callback OAuth, vous recevez :

```json
{
  "access_token": "shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "scope": "read_products,read_orders,read_inventory",
  "expires_in": null,
  "associated_user_scope": "read_products,read_orders,read_inventory"
}
```

Stocker le token immédiatement dans la base de données (voir section 7).

---

## 7. Stocker les credentials dans Michi

```python
# Exemple d'appel après le callback OAuth
from core.security.encryption import encrypt_field

await session.execute(
    insert(StoreCredential).values(
        store_id=store.id,
        encrypted_access_token=encrypt_field(access_token),
        encrypted_api_key=None,
        encrypted_api_secret=None,
        meta={
            "shopify_domain": shop_domain,  # ex: ma-boutique.myshopify.com
            "scopes": granted_scopes,
        }
    )
)
```

### Mapping credentials → connecteur

```python
# Lors de l'ingestion
credentials = {
    "shopify_domain":       store_cred.meta["shopify_domain"],
    "shopify_access_token": decrypt_field(store_cred.encrypted_access_token),
}

await shopify_connector.fetch_all_data(shop_id, credentials=credentials)
```

---

## 8. Passer en production

### Checklist avant activation production

- [ ] `USE_MOCK_SHOPIFY=false` dans `.env.production`
- [ ] `SHOPIFY_API_KEY` et `SHOPIFY_API_SECRET` configurés
- [ ] URL de callback HTTPS enregistrée dans l'app Partners
- [ ] Certificat SSL valide sur `api.michi.app`
- [ ] `ENCRYPTION_KEY` configuré pour chiffrement des tokens
- [ ] Webhook Shopify configuré pour les mises à jour de stock (optionnel)

### Publication de l'app (si distribution publique)

Pour que des marchands tiers installent l'app depuis l'App Store Shopify :

1. Partners Dashboard → votre app → **"Distribution"**
2. Choisir **"Shopify App Store"** (review obligatoire ~2 semaines)
3. Ou **"Custom distribution"** (lien direct, pas de review — recommandé pour Michi SaaS)

> Pour Michi : utiliser **Custom distribution** — l'onboarding Michi guide le marchand vers l'installation sans passer par l'App Store.

---

## 9. Vérification & dépannage

### Test de connexion

```bash
# Appel direct à l'API Shopify pour valider le token
curl -H "X-Shopify-Access-Token: shpat_xxx" \
     "https://ma-boutique.myshopify.com/admin/api/2024-01/shop.json"

# Réponse attendue :
# {"shop": {"id": 123, "name": "Ma Boutique", "domain": "...", ...}}
```

### Erreurs courantes

| Erreur | Cause | Solution |
|---|---|---|
| `401 Unauthorized` | Token révoqué ou mauvais scope | Refaire le flux OAuth |
| `403 Forbidden` | Scope insuffisant | Ajouter le scope manquant dans l'app Partners |
| `429 Too Many Requests` | Rate limit dépassé | Augmenter `_RATE_LIMIT_DELAY` dans `shopify.py` |
| `HMAC validation failed` | Secret incorrect dans le callback | Vérifier `SHOPIFY_API_SECRET` |
| Redirect loop | `redirect_uri` non autorisée | Ajouter l'URL dans les "Allowed redirection URLs" |

### Logs à surveiller

```python
# Dans shopify.py, les logs Loguru :
logger.info("[Shopify] fetch_products : 127 variantes")
logger.error("[Shopify] validate_connection échoué : 401")
```

---

*Retour : [connectors.md](connectors.md)*
