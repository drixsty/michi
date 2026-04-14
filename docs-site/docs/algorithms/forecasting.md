---
id: forecasting
title: Prévisions & Run Rate
sidebar_label: 📈 Prévisions
sidebar_position: 3
---

# Prévisions & Run Rate

Le module de prévision transforme les données nettoyées (sorties du pipeline OOS→IQR)
en indicateurs opérationnels : vitesse de vente, date de rupture, quantité à commander.

**Fichiers concernés :**
- `intelligence/algorithms/run_rate.py`
- `intelligence/algorithms/seasonality.py`
- `intelligence/algorithms/predictions.py`

---

## 1. Run Rate Adaptatif

**Fichier :** `intelligence/algorithms/run_rate.py`

### Définition

Le Run Rate $RR$ est la **vitesse de vente quotidienne** d'un produit en
unités/jour, calculée comme médiane glissante sur les données nettoyées.

### Formule de Base (Fenêtre 30 jours)

Sur une fenêtre glissante $W = 30$ jours, en excluant les jours de rupture
(`is_stockout`) et les outliers (`is_outlier`) :

$$
RR_t^{(30j)} = \tilde{x}\!\left(\{ \hat{y}_i \mid i \in [t-29,\, t],\; \lnot\text{rupture}_i,\; \lnot\text{outlier}_i \}\right)
$$

où $\hat{y}_i$ est la vente corrigée post-nettoyage.

### Détection de Momentum (Tendance Court Terme)

Pour ne pas rater une accélération soudaine (buzz, début de saison), l'algorithme
calcule un **facteur de momentum** comparant la vitesse 7j à la vitesse 30j :

$$
\text{Momentum}_t = \frac{\bar{y}_{t}^{(7j)}}{\bar{y}_{t}^{(30j)}}
$$

Le Run Rate final adapte dynamiquement sa fenêtre selon ce ratio :

$$
RR_t =
\begin{cases}
RR_t^{(7j)} & \text{si } \text{Momentum}_t > 1.2 \text{ (accélération)}\\
RR_t^{(30j)} & \text{si } \text{Momentum}_t < 0.8 \text{ (décélération)}\\
\text{Interpolation linéaire} & \text{sinon (zone neutre)}
\end{cases}
$$

:::tip Interprétation du Momentum
- **Momentum > 1.2 :** Les ventes des 7 derniers jours sont 20% au-dessus de la
  tendance 30j. Fenêtre réduite à 7j pour capturer l'accélération.
- **Momentum < 0.8 :** Ralentissement détecté. Fenêtre 30j pour éviter la surréaction.
- **Zone neutre [0.8–1.2] :** Interpolation pour un changement progressif.
:::

### Fallback (Données insuffisantes)

Si la fenêtre contient moins de `RUN_RATE_MIN_PERIODS = 4` jours valides :

$$
RR_t = \tilde{x}\!\left(\{ \hat{y}_i \mid \lnot\text{rupture}_i,\; \forall i \in \text{série} \}\right)
$$

### Paramètres

| Paramètre | Valeur | Rôle |
|-----------|--------|------|
| `RUN_RATE_WINDOW` | 30 jours | Fenêtre par défaut |
| `RUN_RATE_MIN_PERIODS` | 4 jours | Minimum pour un Run Rate fiable |
| Seuil momentum haut | 1.2 | Déclencheur fenêtre courte |
| Seuil momentum bas | 0.8 | Déclencheur fenêtre longue |
| Fenêtre momentum court | 7 jours | Réactivité aux tendances |

### Edge Cases

| Cas | Comportement |
|-----|-------------|
| Série < 4 jours valides | Fallback médiane globale |
| Tous les jours en rupture | `RR = 0.0` |
| `corrected_units_sold` toujours nul | `RR = 0.0` (pas de consommation) |
| Momentum division par zéro (`medium_term = 0`) | `momentum = 1.0` (neutre) |

### Métriques Qualité

- **Colonne produite :** `run_rate` (float, unités/jour)
- **Invariant :** `run_rate >= 0`
- **Complexité :** $O(n)$ — vectorisation Pandas, interdit les boucles `for`

---

## 2. Facteur de Saisonnalité

**Fichier :** `intelligence/algorithms/seasonality.py`

### Problème

Un produit de mode (beachwear, manteau d'hiver) a une demande cyclique. Le Run Rate
30j peut sous-estimer ou surestimer la demande actuelle selon la phase du cycle.

### Formule du Facteur Saisonnier

Le facteur $\lambda$ est le ratio de la demande récente sur la demande historique :

$$
\lambda = \frac{\bar{y}_{7j}}{\bar{y}_{30j}}
$$

Avec un **caping de sécurité** pour éviter les prédictions aberrantes :

$$
\lambda_{\text{caped}} = \max\!\left(0.5,\; \min\!\left(2.5,\; \lambda\right)\right)
$$

**Seuil de neutralité** — le facteur n'est appliqué que si l'écart est significatif :

$$
\lambda_{\text{final}} =
\begin{cases}
1.0 & \text{si } \lambda_{\text{caped}} \in [0.9,\; 1.1] \\
\lambda_{\text{caped}} & \text{sinon}
\end{cases}
$$

### Paramètres

| Paramètre | Valeur | Rôle |
|-----------|--------|------|
| Fenêtre récente | 7 jours | Demande court terme |
| Fenêtre historique | 30 jours | Tendance de fond |
| Borne inférieure cap | 0.5 | Évite sous-estimation extrême (−50%) |
| Borne supérieure cap | 2.5 | Évite surestimation extrême (+150%) |
| Zone neutre | [0.9, 1.1] | Moins de 10% d'écart → pas d'ajustement |

### Edge Cases

| Cas | Comportement |
|-----|-------------|
| Historique < 14 jours (`window * 2`) | Retourne `1.0` (neutre) |
| `historical_avg <= 0` | Retourne `1.0` (division par zéro évitée) |
| DataFrame vide | Retourne `1.0` |
| Pic > +150% | Caped à `2.5` |

### Métriques Qualité

- **Valeur retournée :** `float` dans $[0.5,\; 2.5]$
- **Application :** le facteur est multiplié au Run Rate avant le calcul de prédiction

---

## 3. Prédiction de Rupture (Stockout Date)

**Fichier :** `intelligence/algorithms/predictions.py`

### Formule

La date de rupture est calculée en divisant le stock actuel par le Run Rate
(corrigé du facteur saisonnier) :

$$
\text{Jours\_restants} = \left\lfloor \frac{S_{\text{actuel}}}{RR_{\text{adaptatif}}} \right\rfloor
$$

$$
\text{Date\_rupture} = \text{Date}_{\text{actuelle}} + \text{Jours\_restants}
$$

### Paramètres

| Paramètre | Type | Description |
|-----------|------|-------------|
| `current_stock` | float ≥ 0 | Stock actuel en unités |
| `run_rate` | float ≥ 0 | Run rate journalier (unités/jour) |
| `reference_date` | date | Date de référence (défaut : `date.today()`) |

### Edge Cases

| Cas | Valeur retournée |
|-----|-----------------|
| `run_rate == 0` | `None` (stock dure indéfiniment, pas de rupture prévisible) |
| `current_stock <= 0` | `reference_date` (rupture immédiate) |
| Stock pour 1000j+ | Date calculée normalement (pas de cap) |

---

## 4. Quantité de Réapprovisionnement (Reorder Qty)

**Fichier :** `intelligence/algorithms/predictions.py`

### Formule

La quantité cible couvre la demande pendant le délai de livraison, avec une marge de
sécurité, puis est arrondie au MOQ (Minimum Order Quantity) supérieur :

$$
Q_{\text{cible}} = RR \times \text{LeadTime}_{\text{effectif}} \times \alpha
$$

où le **délai effectif** intègre les retards historiques du fournisseur (Sprint 8) :

$$
\text{LeadTime}_{\text{effectif}} = \text{LeadTime}_{\text{théorique}} + \delta_{\text{retard}}
$$

$$
Q_{\text{brut}} = \max\!\left(0,\; Q_{\text{cible}} - S_{\text{actuel}}\right)
$$

$$
Q_{\text{recommander}} = \left\lceil \frac{Q_{\text{brut}}}{\text{MOQ}} \right\rceil \times \text{MOQ}
$$

### Paramètres

| Paramètre | Valeur par défaut | Rôle |
|-----------|-------------------|------|
| `safety_factor` $\alpha$ | 1.5 | Marge de sécurité 50% sur le lead time |
| `lead_time` | Fournisseur (jours) | Délai de livraison théorique |
| `average_delay` $\delta$ | 0.0 | Retard moyen constaté (historique fournisseur) |
| `moq` | 1 | Quantité minimale de commande |

:::tip Calibration du Safety Factor
- $\alpha = 1.0$ : couverture exacte du lead time, **aucune marge** (risque de rupture en transit)
- $\alpha = 1.5$ : **recommandé** — absorbe 50% de variabilité (retard, pic de demande)
- $\alpha = 2.0$ : conservateur — adapté aux fournisseurs en Asie avec long lead time
:::

### Edge Cases

| Cas | Comportement |
|-----|-------------|
| `run_rate == 0` | Retourne `0` |
| `lead_time <= 0` | Retourne `0` |
| `current_stock >= Q_cible` | Retourne `0` (stock suffisant) |
| `Q_brut < MOQ` | Retourne `MOQ` (arrondi supérieur forcé) |

### Métriques Qualité

- **Valeur retournée :** `int` ≥ 0, multiple de `moq`
- **Complexité :** $O(1)$ — fonction pure, zéro I/O
- **Test de référence :** `calculate_reorder_quantity(10.0, 7, 50, 20.0) == 100`
