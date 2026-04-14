---
id: forecasting
title: Prévisions & Run Rate
sidebar_label: 📈 Prévisions
sidebar_position: 3
---

# Prévisions & Run Rate

Le Run Rate est l'indicateur de vitesse de croisière d'un produit. C'est l'élément central du calcul de réapprovisionnement.

## 1. Run Rate Adaptatif (Momentum)

Michi 道 calcule une vitesse de vente quotidienne qui s'adapte automatiquement aux changements brusques de tendance.

### Formule de base
Par défaut, le Run Rate ($RR$) est la médiane glissante sur 30 jours :

$$RR_{30j} = \text{median}(\{y_{t-29}, \dots, y_t\})$$

### Momentum (Tendance)
Pour détecter une accélération forte (ex: buzz social, début de saison), nous calculons un ratio de momentum :

$$\text{Momentum} = \frac{\mu_{7j}}{\mu_{30j}}$$

- Si $\text{Momentum} > 1.2$ : L'algorithme bascule sur une fenêtre de **7 jours** pour être plus réactif.
- Sinon : Stabilité sur **30 jours**.

## 2. Projection de Rupture (Stockout)

Nous prédisons la date exacte de fin de stock en croisant le stock actuel et le Run Rate.

### Date de Rupture Estimée
$$\text{Date}_{\text{rupture}} = \text{Date}_{\text{actuelle}} + \left( \frac{\text{Stock}_{\text{actuel}}}{RR_{\text{adaptatif}}} \right)$$

## 3. Quantité de Réassort (Reorder)

La quantité à commander prend en compte le délai de livraison (Lead Time) pour éviter que la rupture ne survienne pendant le transport.

### Formule de Réapprovisionnement
$$Q_{\text{recommander}} = \max(0, (RR \times \text{LeadTime} \times 2) - \text{Stock}_{\text{actuel}})$$

*Note: Le facteur multiplicateur (ici 2) est ajustable selon la politique de stock de sécurité de l'entreprise.*

:::tip Optimisation
Si la quantité calculée est inférieure au **MOQ** (Minimum Order Quantity) du fournisseur, Michi arrondit automatiquement à la valeur du MOQ.
:::
