---
sidebar_position: 2
title: Configuration de Stripe
---

# Configuration de Stripe

Michi utilise **Stripe** pour la gestion de la facturation et des abonnements. L'architecture est prévue pour fonctionner de manière dynamique : les plans tarifaires affichés sur le site sont récupérés directement depuis votre catalogue de produits Stripe.

## 1. Passage en Mode Production

Par défaut, l'application est configurée en mode MOCK. Pour activer Stripe :

Dans le fichier `.env` de votre backend (`apps/api`), modifiez la variable :
```env
BILLING_MODE=STRIPE
```

Ajoutez vos clés d'API secrètes :
```env
STRIPE_API_KEY=sk_live_votre_cle_secrete
STRIPE_WEBHOOK_SECRET=whsec_votre_cle_webhook
```

## 2. Création des Produits et Prix sur Stripe

Pour que les prix s'affichent correctement sur la Landing Page et dans l'Application Web, vous devez créer vos produits sur le Dashboard Stripe.

1. Allez dans **Catalogue de produits** sur Stripe.
2. Créez les 3 produits suivants : **Starter**, **Pro**, et **Entreprise**.
3. **Important (Métadonnées)** : Lors de la création du produit, ajoutez des métadonnées (Metadata) pour aider l'API Michi à les identifier :
   * Clé : `plan_id`, Valeur : `BASIC` (ou `PRO`, ou `ENTERPRISE`)
   * Clé : `is_popular`, Valeur : `true` (uniquement pour le plan Pro afin de le mettre en avant)
4. Dans la section **Fonctionnalités (Features)** du produit Stripe, ajoutez les puces que vous souhaitez afficher sur les cartes de prix du site (ex: "Jusqu'à 50k$/mois de CA").
5. Ajoutez les prix récurrents mensuels.

Une fois créés, récupérez les **ID des prix** (ex: `price_1N2M3...`) et placez-les dans le `.env` de l'API :
```env
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

## 3. Configuration des Webhooks Stripe

Pour que l'application soit avertie lorsqu'un paiement est réussi ou échoue, vous devez configurer un Webhook Stripe pointant vers l'API Michi.

1. Dans le Dashboard Stripe, allez dans **Développeurs > Webhooks**.
2. Cliquez sur **Ajouter un endpoint**.
3. URL de l'endpoint : `https://api.michi.app/webhooks/stripe`
4. Sélectionnez les événements à écouter :
   * `checkout.session.completed` : Utilisé pour activer un abonnement après l'essai.
   * `customer.subscription.updated` : Utilisé pour modifier le statut d'abonnement.
   * `customer.subscription.deleted` : Utilisé pour révoquer l'accès lors d'une résiliation.
   * `invoice.paid` : Utilisé pour l'historique des factures.
5. Copiez le "Secret de signature" (`whsec_...`) et mettez-le dans `STRIPE_WEBHOOK_SECRET` de votre fichier `.env`.

## 4. Test avec l'essai de 7 jours

Michi inclut nativement une logique d'essai de 7 jours obligatoires.
Dès l'inscription d'une nouvelle organisation, l'API lui attribue :
- Statut de l'abonnement : `TRIALING`
- Expiration : `Date du jour + 7 jours`

Tant que l'essai est actif, l'utilisateur a un accès total sans moyen de paiement.
Une fois l'essai expiré, le composant `OnboardingGuard` (côté Web) et le décorateur `@require_permission` (côté API) bloquent l'accès à l'application et redirigent l'utilisateur vers la page `/pricing` pour l'obliger à s'abonner via Stripe.
