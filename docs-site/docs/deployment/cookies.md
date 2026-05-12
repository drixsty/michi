---
sidebar_position: 3
title: Cookies & RGPD
---

# Configuration des Cookies et Conformité RGPD

Le projet Michi dispose d'un système de gestion des cookies (Cookie Consent) pour assurer la conformité avec la réglementation RGPD (Règlement Général sur la Protection des Données).

Le système se trouve au sein de la Landing Page (`apps/landing/src/components/common/CookieConsent.tsx`).

## 1. Fonctionnement du Bandeau de Cookies

Dès la première visite d'un utilisateur, une modale compacte apparaît en bas de l'écran. 
Elle offre trois options à l'utilisateur :
- **Tout Accepter** : Active les cookies essentiels, statistiques et marketing.
- **Tout Refuser** : N'active que les cookies essentiels.
- **Paramétrer** : Ouvre une fenêtre détaillée permettant d'activer chaque catégorie indépendamment.

Les choix sont stockés dans un cookie côté client nommé `michi_cookie_consent`, qui expire après 365 jours.

## 2. Intégration des Scripts Tiers (Google Analytics, Pixels)

Pour être en conformité stricte avec le RGPD, vous ne devez **jamais** charger de scripts de tracking avant que l'utilisateur n'ait donné son consentement explicite.

L'application expose les choix de l'utilisateur à l'échelle globale (si vous utilisez le composant `CookieConsent`). Vous pouvez écouter la présence du cookie `michi_cookie_consent` ou utiliser une logique pour conditionner l'injection de scripts (ex: GTM, Google Analytics, Pixel Facebook).

**Exemple d'injection conditionnelle via Next.js :**

```tsx
import { useEffect, useState } from 'react';
import Script from 'next/script';

export function Analytics() {
  const [consentGiven, setConsentGiven] = useState(false);

  useEffect(() => {
    // Vérifie si le consentement pour l'analytique est accordé
    const match = document.cookie.match(new RegExp('(^| )michi_cookie_consent=([^;]+)'));
    if (match) {
      try {
        const prefs = JSON.parse(decodeURIComponent(match[2]));
        if (prefs.analytics) setConsentGiven(true);
      } catch (e) {}
    }
  }, []);

  if (!consentGiven) return null;

  return (
    <Script
      strategy="afterInteractive"
      src={`https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXX`}
    />
  );
}
```

## 3. Personnalisation du Design

Le design du bandeau de cookies a été pensé pour être minimaliste et s'intégrer parfaitement avec la Landing Page (inspiré des designs Vercel/Linear). 
Si vous souhaitez modifier les couleurs ou l'arrondi (border-radius) pour qu'ils collent à une autre marque, vous pouvez :

- Modifier les classes Tailwind dans `CookieConsent.tsx`.
- Adapter les couleurs via vos variables de thème CSS globales (`apps/landing/src/app/globals.css`).

## 4. Internationalisation (i18n)

Le texte du bandeau de cookies, des catégories et des descriptions légales est géré dynamiquement par `next-intl`. Vous devez vous assurer que les clés `cookieConsent` existent dans vos fichiers `fr.json` et `en.json` (dans `apps/landing/messages/`).
