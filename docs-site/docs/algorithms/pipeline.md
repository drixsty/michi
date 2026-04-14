---
id: pipeline
title: Pipeline de Nettoyage
sidebar_label: 🧼 Nettoyage
sidebar_position: 2
---

# Pipeline de Nettoyage

Avant toute prévision, Michi 道 nettoie l'historique des ventes pour éliminer les bruits qui faussent les calculs.

## 1. Correction des Ruptures (OOS)

Lorsqu'un produit est en rupture de stock, les ventes enregistrées sont de 0, ce qui ne reflète pas la **demande réelle**. Michi calcule une demande théorique pour ces périodes.

### Formule
Pour chaque jour $t$ où le stock est nul ($S_t = 0$), la vente réelle $y_t$ est remplacée par la demande théorique $\hat{y}_t$ :

$$\hat{y}_t = \frac{1}{N} \sum_{i=t-14}^{t-1} y_i \quad \text{où } S_i > 0$$

- **Fenêtre :** 14 jours de ventes connues (non nulles).
- **Objectif :** Éviter de sous-estimer la vitesse de vente future.

## 2. Détection d'Outliers (IQR)

Les pics de ventes anormaux sont détectés via la méthode de l'**Interquartile Range (IQR)**.

### Calcul des Bornes
On définit $Q_1$ (25e percentile) et $Q_3$ (75e percentile) de la série temporelle.

$$IQR = Q_3 - Q_1$$
$$\text{Borne Haute} = Q_3 + 1.5 \times IQR$$

### Détection
Un point de donnée $y_t$ est marqué comme **outlier** si :
$$y_t > \text{Borne Haute}$$

### Correction
Les outliers sont lissés en utilisant une **médiane glissante centrée** pour préserver le contexte local :

$$y_{t, \text{corrected}} = \text{median}(\{y_{t-5}, \dots, y_{t+5}\})$$

:::warning Pourquoi pas de Borne Basse ?
En prévision de stock, les valeurs anormalement basses (hors rupture) sont considérées comme une vraie faible demande. Utiliser une borne basse de type $Q_1 - 1.5 \times IQR$ générerait trop de faux positifs sur les périodes creuses, dégradant la précision (MAPE).
:::
