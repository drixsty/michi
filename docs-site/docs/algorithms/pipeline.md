---
id: pipeline
title: Pipeline de Nettoyage
sidebar_label: 🧼 Nettoyage des Données
sidebar_position: 2
---

# Pipeline de Nettoyage

Avant toute prévision, Michi 道 nettoie l'historique des ventes pour éliminer les biais
qui faussent les prédictions. Le pipeline s'exécute **en séquence** dans
[`intelligence/pipeline/cleaning_pipeline.py`](https://github.com) :

```
Données brutes → [1. Correction OOS] → [2. Détection Outliers] → Données nettoyées
```

> **Principe de conception :** le module `intelligence/` est une **fonction pure** — zéro import SQLAlchemy, zéro I/O. Il reçoit un `DataFrame`, renvoie un `DataFrame`.

---

## 1. Correction des Ruptures de Stock (OOS)

**Fichier :** `intelligence/algorithms/out_of_stock_correction.py`

### Problème

Quand un produit est en rupture (`end_of_day_stock = 0`), les ventes enregistrées
sont `0` — non pas parce que la demande est nulle, mais parce qu'il n'y avait rien
à vendre. Sans correction, le Run Rate sera sous-estimé, entraînant des **ruptures
en cascade**.

### Formule

Pour chaque jour $t$ où le stock de fin de journée est nul ($S_t = 0$), la vente
réelle $y_t$ est remplacée par la demande théorique $\hat{y}_t$ :

$$
\hat{y}_t = \tilde{x}\!\left(\{ y_i \mid i \in [t-14,\, t-1],\; S_i > 0 \}\right)
$$

où $\tilde{x}(\cdot)$ désigne la **médiane** de l'ensemble.

**Fallback** (fenêtre insuffisante) — si aucun jour non-rupture n'existe dans les
14 jours précédents :

$$
\hat{y}_t = \tilde{x}\!\left(\{ y_i \mid S_i > 0,\; \forall i \in \text{série} \}\right)
$$

> **Pourquoi la médiane, pas la moyenne ?**  
> Sprint 4 — DS-1 : si un pic (Black Friday ×10) tombe dans la fenêtre pré-rupture,
> la **moyenne** surestime la demande corrigée. La **médiane** est insensible aux
> valeurs extrêmes.

### Paramètres

| Paramètre | Valeur | Rôle |
|-----------|--------|------|
| `ROLLING_WINDOW` | 14 jours | Fenêtre de la médiane glissante |
| Condition de rupture | `end_of_day_stock == 0` | Détection jour de rupture |
| Borne inférieure | `clip(lower=0)` | Garantit des ventes non-négatives |

### Edge Cases

| Cas | Comportement |
|-----|-------------|
| Produit toujours en rupture (100% de la série) | `global_median = 0.0` → $\hat{y}_t = 0$ |
| Fenêtre < 1 jour valide | Fallback médiane globale de la série |
| `units_sold < 0` (correction importateur) | Conservé tel quel (pas de modification) |
| Données non triées | `sort_values("date")` appliqué en entrée |

### Métriques Qualité

- **Colonne produite :** `theoretical_units_sold`
- **Colonne indicateur :** `is_stockout` (bool)
- **Invariant :** `theoretical_units_sold >= 0` toujours

---

## 2. Détection et Correction des Outliers (IQR)

**Fichier :** `intelligence/algorithms/outlier_detection.py`

### Problème

Des pics anormalement hauts (erreurs de saisie, doublons de commandes B2B) peuvent
faire croire à une demande 5-10× supérieure à la réalité. Un tel point fausse la
médiane glissante et génère du surstockage.

### Détection — Méthode IQR

On calcule les percentiles $Q_1$ et $Q_3$ des ventes **non-rupture** sur toute la
série (ou une fenêtre glissante si `iqr_window` est défini) :

$$
\text{IQR} = Q_3 - Q_1
$$

$$
B_{\text{haute}} = Q_3 + 1.5 \times \text{IQR}
$$

Un jour $t$ est marqué **outlier** si et seulement si :

$$
y_t > B_{\text{haute}} \quad \text{ET} \quad \texttt{is\_stockout}_t = \text{False}
$$

:::warning Pourquoi pas de borne basse ?
Les valeurs anormalement **basses** (hors rupture) représentent une vraie faible
demande (période creuse, produit en fin de vie). Appliquer $B_{\text{basse}} = Q_1 - 1.5 \times \text{IQR}$
génèrerait des faux positifs sur les périodes naturellement calmes, dégradant le MAPE.
:::

### Correction des Outliers

Les outliers sont remplacés par la **médiane glissante centrée** sur 11 jours des
jours **non-outlier, non-rupture** précédents :

$$
y_{t,\text{corrigé}} = \tilde{x}\!\left(\{ y_i \mid i \in [t-5,\, t+5],\; \lnot\text{outlier}_i,\; \lnot\text{rupture}_i \}\right)
$$

**Fallback :** si la fenêtre centrée ne contient pas assez de jours valides, on
utilise la médiane globale de la série.

### Paramètres

| Paramètre | Valeur | Rôle |
|-----------|--------|------|
| `OUTLIER_ROLLING_WINDOW` | 11 jours | Fenêtre centrée pour la correction |
| `iqr_window` | `None` (global) | Fenêtre glissante IQR (opt.) |
| `IQR_SEASONAL_WINDOW` | 90 jours | Recommandé pour produits saisonniers |
| Multiplicateur IQR | 1.5 | Sensibilité standard (Tukey, 1977) |

### IQR Glissant (DS-2 Sprint 4)

Pour les produits à forte saisonnalité (ex : beachwear), un IQR global flagge à tort
les ventes hivernales comme normales et les pics estivaux comme outliers. Avec
`iqr_window=90`, les bornes sont recalculées localement :

$$
B_{\text{haute},t} = Q_{3,t}^{(90j)} + 1.5 \times \text{IQR}_t^{(90j)}
$$

### Edge Cases

| Cas | Comportement |
|-----|-------------|
| Série < 4 points | Aucun outlier détecté (`iqr_window` ignoré) |
| `Q1 == Q3` (série constante) | `IQR = 0` → $B_{\text{haute}} = Q_3$ → seuls les pics stricts sont outliers |
| Jour de rupture avec vente haute | Jamais flaggé outlier (`is_stockout` prioritaire) |
| `theoretical_units_sold` présent | Utilisé à la place de `units_sold` |

### Métriques Qualité

- **Colonnes produites :** `is_outlier` (bool), `corrected_units_sold` (float), `iqr_lower` (float), `iqr_upper` (float)
- **Invariant :** `corrected_units_sold >= 0` toujours
- **Objectif :** MAPE du Run Rate en aval < 20% sur séries synthétiques de test
