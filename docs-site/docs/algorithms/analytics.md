---
id: analytics
title: Scoring & Analytics
sidebar_label: 📊 Analytics
sidebar_position: 4
---

# Scoring & Analytics

Le module analytics de Michi 道 transforme les données produits agrégées en **indicateurs
de décision stratégique**. Contrairement aux algorithmes de nettoyage, ces fonctions
sont **O(1) ou O(n log n)** et s'exécutent sur des agrégats — pas sur des séries temporelles.

**Fichiers concernés :**
- `intelligence/algorithms/abc_analysis.py`
- `intelligence/analytics/health_score.py`
- `intelligence/analytics/financial_kpis.py`
- `intelligence/analytics/risk_scoring.py`

---

## 1. Analyse ABC (Classification Pareto)

**Fichier :** `intelligence/algorithms/abc_analysis.py`

### Problème

Tous les produits ne méritent pas la même attention. L'analyse ABC identifie les
produits qui génèrent l'essentiel de la **marge brute** pour les traiter en priorité.

### Formule du Profit Brut Annualisé

Pour chaque produit $i$, on calcule sa contribution financière projetée sur un an :

$$
P_i^{\text{annuel}} = (\text{prix\_vente}_i - \text{prix\_achat}_i) \times (RR_i \times 365)
$$

### Classification Pareto (Seuils 70 / 90 / 100)

Les produits sont triés par $P_i^{\text{annuel}}$ décroissant, puis classés selon le
**pourcentage cumulé de profit** dans l'organisation :

$$
\text{cum\_pct}_k = \frac{\sum_{i=1}^{k} P_i^{\text{annuel}}}{\sum_{i=1}^{N} P_i^{\text{annuel}}}
$$

| Rang | Condition | Priorité Stratégique |
|------|-----------|----------------------|
| **A** | $\text{cum\_pct}_k \leq 70\%$ | **Critique** — Zéro tolérance rupture |
| **B** | $70\% < \text{cum\_pct}_k \leq 90\%$ | **Important** — Suivi hebdomadaire |
| **C** | $\text{cum\_pct}_k > 90\%$ | **Secondaire** — Optimisation MOQ |

:::info Règle Pareto inversée
En e-commerce mode/beauté, ~20% des SKUs génèrent ~80% de la marge. L'analyse ABC
permet d'allouer les efforts (stocks de sécurité, alertes prioritaires) là où l'impact
financier est maximal.
:::

### Paramètres

| Paramètre | Type | Description |
|-----------|------|-------------|
| `product_id` | str | Identifiant unique du produit |
| `run_rate` | float | Run rate journalier (unités/jour) |
| `sale_price` | float | Prix de vente unitaire (€) |
| `cost_price` | float | Prix d'achat unitaire (€) |

### Edge Cases

| Cas | Comportement |
|-----|-------------|
| `annual_gross_profit <= 0` | Rang `C` par défaut |
| `sale_price == cost_price` | `unit_margin = 0` → Rang `C` |
| DataFrame vide | Retourné tel quel sans modification |
| Tous profits négatifs | Warning loggé, tous en `C` |
| Un seul produit dominant (> 70% profit) | Rang `A` (cumul atteint dès le 1er) |

### Métriques Qualité

- **Colonnes produites :** `annual_gross_profit`, `abc_rank` (A/B/C)
- **Complexité :** $O(n \log n)$ — un tri par profit décroissant
- **Invariant :** chaque produit reçoit exactement un rang parmi {A, B, C}

---

## 2. Health Score (Score de Santé Inventaire)

**Fichier :** `intelligence/analytics/health_score.py`

### Définition

Le Health Score est une **note de 0 à 100** évaluant la performance globale de la
chaîne d'approvisionnement d'un store sur 3 piliers.

### Formule Générale

$$
H = \text{round}\!\left(\min\!\left(100,\; \max\!\left(0,\; (0.5 \cdot \text{Avail} + 0.3 \cdot \text{Rot} + 0.2 \cdot \text{Out}) \times 100\right)\right)\right)
$$

### Composante 1 — Disponibilité CA (Avail, poids 50%)

Mesure la proportion du chiffre d'affaires **non menacé** par des ruptures :

$$
\text{CA\_potentiel} = RR_{\text{total}} \times 30 \times \bar{p}_{\text{vente}} + \text{CA\_risque}
$$

$$
\text{Avail} = 1 - \frac{\text{CA\_risque}}{\text{CA\_potentiel}}
$$

### Composante 2 — Rotation du Stock (Rot, poids 30%)

Pénalise les stocks trop bas (risque rupture) **et** les stocks trop élevés
(immobilisation de capital) :

$$
\text{Rot} =
\begin{cases}
\dfrac{\text{Couv}}{7} & \text{si } \text{Couv} < 7j \quad \text{(stock critique)} \\[10pt]
1.0 & \text{si } 7j \leq \text{Couv} \leq 45j \quad \text{(optimal)} \\[10pt]
1 - \dfrac{\text{Couv} - 45}{45} & \text{si } 45j < \text{Couv} \leq 90j \quad \text{(sur-stockage léger)} \\[10pt]
\max\!\left(0,\; 0.5 - \dfrac{\text{Couv} - 90}{180}\right) & \text{si } \text{Couv} > 90j \quad \text{(sur-stockage fort)}
\end{cases}
$$

### Composante 3 — Taux de Disponibilité (Out, poids 20%)

$$
\text{Out} = 1 - \frac{\text{SKU en rupture}}{\text{SKU totaux actifs}}
$$

### Interprétation du Score

| Plage | Couleur | Signification |
|-------|---------|---------------|
| 80 – 100 | 🟢 Vert | Gestion saine — aucune action urgente |
| 50 – 79 | 🟡 Orange | Surveillance — réapprovisionnement partiel requis |
| 0 – 49 | 🔴 Rouge | Critique — réapprovisionnement immédiat produits A |

### Paramètres d'Entrée

| Paramètre | Type | Description |
|-----------|------|-------------|
| `revenue_at_risk` | float | CA à risque (somme des reorder_qty × sale_price) |
| `total_run_rate` | float | Run rate total journalier tous SKUs |
| `avg_sale_price` | float | Prix de vente moyen |
| `avg_coverage_days` | float | Couverture moyenne en jours |
| `stockout_count` | int | Nombre de SKUs avec stock ≤ 0 |
| `total_skus` | int | Nombre total de SKUs actifs |

### Edge Cases

| Cas | Comportement |
|-----|-------------|
| `total_skus == 0` | `Out = 1.0` (pas de rupture possible) |
| `CA_potentiel == 0` | `Avail = 1.0` (pas de CA en jeu) |
| `avg_coverage_days > 270j` | `Rot → 0` (sur-stockage extrême) |
| Score < 0 | Clampé à 0 |
| Score > 100 | Clampé à 100 |

### Métriques Qualité

- **Valeur retournée :** `int` dans $[0, 100]$
- **Complexité :** $O(1)$ — fonction pure
- **Test de référence :** `calculate_health_score(0, 10, 50, 30, 0, 100) == 100`

---

## 3. KPIs Financiers (Financial KPIs)

**Fichier :** `intelligence/analytics/financial_kpis.py`

### Définition

Agrège les métriques financières de l'ensemble des SKUs d'un store pour le dashboard
décisionnel.

### Formules

**Valeur d'inventaire (coût) :**
$$
V_{\text{coût}} = \sum_{i=1}^{N} S_i \times p_i^{\text{achat}}
$$

**Valeur d'inventaire (marché) :**
$$
V_{\text{vente}} = \sum_{i=1}^{N} S_i \times p_i^{\text{vente}}
$$

**CA à risque** (somme des valeurs de réapprovisionnement urgents) :
$$
\text{CA\_risque} = \sum_{i \in \text{risque}} Q_i^{\text{reorder}} \times p_i^{\text{vente}}
$$

**Couverture moyenne en jours** (sur SKUs avec run rate > 0) :
$$
\overline{\text{Couv}} = \frac{1}{M} \sum_{i=1}^{M} \frac{S_i}{RR_i}
\quad \text{où } M = |\{i \mid RR_i > 0\}|
$$

**Prix de vente moyen pondéré par le stock :**
$$
\bar{p}_{\text{vente}} = \frac{V_{\text{vente}}}{\sum_{i} S_i}
$$

### Paramètres d'Entrée

Le dictionnaire `sku_aggregation` produit par `decisions/service.py` avec pour chaque SKU :

| Clé | Type | Description |
|-----|------|-------------|
| `stock` | int | Stock actuel |
| `cost` | float | Prix d'achat unitaire (€) |
| `sale` | float | Prix de vente unitaire (€) |
| `run_rate` | float | Run rate journalier |
| `risk_value` | float | CA à risque pour ce SKU |
| `coverage_days` | float | Couverture calculée par `risk_scoring` |

### Edge Cases

| Cas | Comportement |
|-----|-------------|
| Aucun SKU avec `run_rate > 0` | `stock_coverage_avg_days = 0.0` |
| `total_stock == 0` | `avg_sale_price = 0.0` |
| `risk_value` manquant | Traité comme `0.0` |

### Métriques Qualité

- **Dataclass retournée :** `FinancialKpis` (frozen, immutable)
- **Complexité :** $O(n)$ vectorisé
- **Précision :** arrondi à 2 décimales (€)

---

## 4. Scoring de Risque (Risk Scoring)

**Fichier :** `intelligence/analytics/risk_scoring.py`

### Définition

Calcule un **score de risque financier** par SKU et trie les produits par priorité
d'action décroissante.

### Formule du Score de Risque

Le score de risque $\rho_i$ d'un SKU est calculé par `decisions/service.py` (premier
pass) et injecté dans `sku_aggregation`. La formule intègre :

$$
\rho_i = Q_i^{\text{reorder}} \times p_i^{\text{vente}}
$$

Soit la **valeur de la marchandise manquante** à commander — plus cette valeur est
haute, plus le risque financier est élevé.

### Couverture en Jours

Pour chaque SKU, `score_products()` calcule la couverture :

$$
\text{Couv}_i =
\begin{cases}
\dfrac{S_i}{RR_i} & \text{si } RR_i > 0 \\
999.0 & \text{si } RR_i = 0 \quad \text{(stock "infini")}
\end{cases}
$$

### Date de Rupture SKU

$$
\text{Date\_rupture}_i = \text{Aujourd'hui} + \max\!\left(0,\; \lfloor\text{Couv}_i\rfloor\right)
$$

Si $RR_i = 0$, `stockout_date = None`.

### Tri de Priorité

Les SKUs sont triés par **score de risque décroissant** pour afficher en tête du
tableau de bord les produits qui représentent la plus grande valeur à risque :

$$
\text{risk\_items}_{\text{sorted}} = \text{sort}\!\left(\{(\rho_i, \text{SKU}_i)\},\; \text{desc}\right)
$$

### Paramètres

| Champ `RiskItem` | Type | Description |
|-----------------|------|-------------|
| `product_id` | str | ID produit |
| `sku` | str | Code SKU |
| `risk_value` | float | Score de risque ($\rho_i$, arrondi 2 déc.) |
| `stockout_date` | date \| None | Date prévisionnelle de rupture |
| `reorder_quantity` | int | Quantité à commander |
| `days_of_stock` | float | Couverture en jours (arrondi 1 déc.) |
| `run_rate` | float | Run rate journalier (arrondi 4 déc.) |
| `cost_price` | float | Prix d'achat (€) |
| `sale_price` | float | Prix de vente (€) |

### Métriques Qualité

- **Type retourné :** `tuple[list[RiskItem], float]` — liste triée + couverture moyenne
- **Complexité :** $O(n \log n)$ — un tri final
- **Invariant :** `days_of_stock >= 0`, `coverage_days == 999.0` si `run_rate == 0`
- **Immutabilité :** `RiskItem` est une `@dataclass(frozen=True)` — thread-safe

### Edge Cases

| Cas | Comportement |
|-----|-------------|
| `sku_aggregation` vide | Liste vide, `avg_coverage_days = 0.0` |
| Aucun SKU avec `run_rate > 0` | `avg_coverage_days = 0.0` |
| `platforms` de type `set` ou `list` | Converti en string trié par virgule |
| `risk_value` non fourni | Défaut `0.0` |
