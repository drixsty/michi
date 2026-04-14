---
id: analytics
title: Scoring & Analytics
sidebar_label: 📊 Analytics
sidebar_position: 4
---

# Scoring & Analytics

Michi 道 transforme les données brutes en indicateurs de décision stratégique via des scorings multicritères.

## 1. Analyse ABC (Pareto Financement)

L'analyse ABC classifie les produits selon leur contribution à la **Marge Brute Annualisée**.

### Formule du Profit Brut Annuel ($P_a$)
$$P_a = (\text{Prix}_{\text{vente}} - \text{Prix}_{\text{achat}}) \times (RR \times 365)$$

### Classification
Les produits sont triés par $P_a$ décroissant, puis classés selon leur pourcentage cumulé dans le profit total de l'organisation :

| Rang | % Profit Cumulé | Priorité Stratégique |
|------|-----------------|----------------------|
| **A** | Top 70% | **Critique** — Jamais de rupture |
| **B** | 70% à 90% | **Important** — Suivi régulier |
| **C** | 90% à 100% | **Secondaire** — Optimisation MOQ |

## 2. Health Score (Score de Santé)

Le Health Score est une note globale de 0 à 100 évaluant la performance de la chaîne d'approvisionnement d'un store.

### Composantes
Le score est une moyenne pondérée de trois piliers ($H = 0.5 \cdot \text{Avail} + 0.3 \cdot \text{Rot} + 0.2 \cdot \text{Out}$) :

#### A. Disponibilité du CA (Avail)
$$Avail = 1 - \frac{\text{CA à Risque}}{\text{CA Potentiel}}$$

#### B. Rotation du Stock (Rot)
Indique si le stock est trop bas ou trop élevé par rapport à la demande.
- Si $\text{Couverture} < 7j$ : $\text{Rot} = \frac{\text{Couv}}{7}$
- Si $7j \leq \text{Couverture} \leq 45j$ : $\text{Rot} = 1.0$ (Optimal)
- Si $\text{Couverture} > 45j$ : Dégradation progressive du score.

#### C. Taux de Rupture (Out)
$$Out = 1 - \frac{\text{SKU en rupture}}{\text{SKU totaux}}$$

:::tip Interprétation
Un Health Score $> 80$ indique une gestion saine. Un score $< 50$ nécessite un réapprovisionnement immédiat des produits de rang A.
:::
