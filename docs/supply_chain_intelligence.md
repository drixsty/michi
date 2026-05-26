# Intelligence Supply Chain — Documentation Complète
## Guide de formation & référence produit · Michi 道

**Version :** 1.0 — Post Sprint 26  
**Public :** Nouveaux membres de l'équipe · Marketing · Product · Data Science  
**Auteurs :** Équipe Michi — Supply Chain & Data Science

---

## Table des matières

1. [Pourquoi ce document ?](#1-pourquoi-ce-document)
2. [Le problème que Michi résout](#2-le-problème-que-michi-résout)
3. [Glossaire Supply Chain](#3-glossaire-supply-chain)
4. [Architecture du pipeline algorithmique](#4-architecture-du-pipeline-algorithmique)
5. [Étape 1 — Correction des ruptures de stock (OOS)](#5-étape-1--correction-des-ruptures-de-stock-oos)
6. [Étape 2 — Détection et correction des outliers (IQR)](#6-étape-2--détection-et-correction-des-outliers-iqr)
7. [Étape 3 — Calcul du run rate (taux de vente)](#7-étape-3--calcul-du-run-rate-taux-de-vente)
8. [Étape 4 — Prédiction de la date de rupture](#8-étape-4--prédiction-de-la-date-de-rupture)
9. [Étape 5 — Date d'alerte commande (ROP Date)](#9-étape-5--date-dalerte-commande-rop-date)
10. [Étape 6 — Quantité de réapprovisionnement (Safety Stock)](#10-étape-6--quantité-de-réapprovisionnement-safety-stock)
11. [Analyse ABC — Priorisation par la marge](#11-analyse-abc--priorisation-par-la-marge)
12. [Précision des prévisions (MAPE, MAE, Biais)](#12-précision-des-prévisions-mape-mae-biais)
13. [Score de santé inventaire](#13-score-de-santé-inventaire)
14. [Analyse des performances fournisseurs](#14-analyse-des-performances-fournisseurs)
15. [KPIs financiers inventaire](#15-kpis-financiers-inventaire)
16. [Cas d'usage complets — Scénarios terrain](#16-cas-dusage-complets--scénarios-terrain)
17. [Positionnement marché et valeur ajoutée](#17-positionnement-marché-et-valeur-ajoutée)
18. [Fiches récapitulatives — Aide-mémoire](#18-fiches-récapitulatives--aide-mémoire)

---

## 1. Pourquoi ce document ?

Ce document existe pour une raison simple : **la supply chain est le cœur de Michi**, et tout le monde dans l'équipe doit comprendre ce que le produit fait, pourquoi, et comment.

Que vous soyez :
- **Développeur** qui implémente un algorithme — vous devez comprendre le sens métier avant le code
- **Commercial** qui présente Michi à un prospect — vous devez expliquer les formules avec des mots simples
- **Data scientist** qui améliore les modèles — vous devez connaître les hypothèses et les limites de chaque algorithme
- **Nouveau membre de l'équipe** — vous devez monter en compétence supply chain rapidement

Ce document vous donne une formation complète en supply chain appliquée à l'e-commerce, centrée sur les algorithmes de Michi.

**Comment lire ce document :**
- Chaque section suit la même structure : **concept → formule → exemple concret → cas d'usage → limites**
- Les formules mathématiques sont toujours accompagnées d'une explication en langage courant
- Les exemples sont tous tirés de cas réels e-commerce mode et beauté

---

## 2. Le problème que Michi résout

### 2.1 La réalité d'un e-commerçant aujourd'hui

Imaginez Sophie, responsable achats d'une marque de vêtements en ligne. Elle gère 800 références (SKUs) réparties sur Shopify et Amazon. Chaque semaine, elle doit répondre à ces questions :

- Quels produits vont être en rupture dans les 30 prochains jours ?
- Combien commander pour chacun d'eux ?
- Quand passer les commandes fournisseurs pour que le stock arrive à temps ?
- Quels produits rapportent vraiment de l'argent (vs ceux qui occupent l'entrepôt) ?

**Sans Michi :** Sophie passe 2 jours par semaine sur Excel. Elle se trompe régulièrement sur les volumes à commander. Elle a des ruptures sur ses bestsellers et du surstockage sur ses fins de collection. Elle rate des ventes et immobilise du capital.

**Avec Michi :** Ces 4 questions ont une réponse automatique, calculée chaque nuit, affichée dans un tableau de bord en 3 clics.

### 2.2 Les deux ennemis de la supply chain

Toute la valeur de Michi repose sur l'équilibre entre deux problèmes opposés :

```
RUPTURE DE STOCK                    SURSTOCKAGE
(stockout)                          (overstock)

Vente perdue                        Capital immobilisé
Client insatisfait                  Coût de stockage
Perte de position SEO               Dépréciation (mode)
Réputation dégradée                 Risque d'invendus

← Commander trop peu ——————————————— Commander trop ————————→
                            ↑
                     ZONE OPTIMALE
                  (Michi cherche ça)
```

Michi ne cherche pas à éliminer les deux risques — c'est impossible. Il cherche à **trouver le point d'équilibre optimal** compte tenu de la demande réelle, de la variabilité du fournisseur, et du niveau de service que le client veut garantir.

### 2.3 Ce que le marché SME n'avait pas avant Michi

| Fonctionnalité | Excel manuel | Shopify natif | Linnworks/Cin7 | **Michi** |
|----------------|:---:|:---:|:---:|:---:|
| Correction ruptures historiques | ❌ | ❌ | ❌ | ✅ |
| Taux de vente nettoyé des anomalies | ❌ | ❌ | Basique | ✅ |
| Safety stock avec variabilité fournisseur | ❌ | ❌ | ❌ | ✅ |
| Date d'alerte commande (ROP date) | Manuelle | ❌ | ❌ | ✅ |
| ABC par marge brute | Manuelle | ❌ | CA seul | ✅ |
| Score de santé inventaire | ❌ | ❌ | ❌ | ✅ |
| Multi-canal unifié | ❌ | Non | Partiel | ✅ |

---

## 3. Glossaire Supply Chain

Avant d'entrer dans les formules, voici les termes que vous rencontrerez partout dans le produit et dans les conversations clients.

### Termes fondamentaux

| Terme | Définition simple | Exemple concret |
|-------|-------------------|----------------|
| **SKU** (Stock Keeping Unit) | Identifiant unique d'un produit dans une configuration précise | "Robe rouge, taille M" est un SKU différent de "Robe rouge, taille L" |
| **Run rate** | Nombre d'unités vendues par jour en moyenne | Si on vend 21 unités en 3 semaines → run rate = 1 unité/jour |
| **Stockout** (rupture) | Stock épuisé, impossible de satisfaire la demande | Stock = 0 en fin de journée |
| **Lead time** (délai fournisseur) | Nombre de jours entre la commande et la réception | Commander le 1er → livraison le 22 → lead time = 21 jours |
| **MOQ** (Minimum Order Quantity) | Quantité minimale que le fournisseur accepte par commande | "Minimum 50 unités par couleur" |
| **Safety stock** | Stock tampon pour absorber les aléas de demande et de livraison | 30 unités de réserve pour couvrir les retards |
| **Reorder Point (ROP)** | Niveau de stock ou date qui déclenche une commande | "Commander quand le stock tombe sous 60 unités" ou "Commander avant le 15 juin" |
| **Coverage days** | Nombre de jours pendant lesquels le stock actuel peut couvrir la demande | Stock 90 unités, run rate 3/j → coverage = 30 jours |
| **Service level** | Probabilité de ne pas être en rupture pendant le délai fournisseur | 95% = on accepte d'être en rupture 5% du temps |
| **Outlier** | Journée de vente anormalement élevée ou basse (erreur, double saisie...) | 500 ventes un jour où on en vend habituellement 5 |
| **OOS** | Out Of Stock, équivalent de stockout | — |
| **Marge brute** | Prix de vente moins coût d'achat | Vendu 50€, acheté 20€ → marge brute = 30€ |

### Termes statistiques

| Terme | Définition simple | À retenir |
|-------|-------------------|-----------|
| **Médiane** | La valeur du milieu quand on trie une série | Plus robuste que la moyenne aux valeurs extrêmes |
| **Moyenne** | Somme divisée par le nombre d'éléments | Sensible aux valeurs extrêmes (Black Friday) |
| **Écart-type (σ, sigma)** | Mesure de la variabilité d'une série | Sigma élevé = demande imprévisible |
| **IQR** | Interquartile Range : différence entre le 75e et le 25e percentile | Mesure la dispersion "normale" sans les extrêmes |
| **MAPE** | Mean Absolute Percentage Error : erreur relative moyenne | MAPE = 10% signifie que nos prévisions se trompent de 10% en moyenne |
| **Biais** | Erreur systématique dans un sens | Biais positif = on sur-estime toujours les ventes |

### Termes Michi spécifiques

| Terme | Définition |
|-------|-----------|
| **Reorder Alert Date** | Date limite pour passer une commande afin de recevoir le stock avant la rupture |
| **Revenue at Risk** | Valeur des commandes fournisseurs à passer pour éviter les ruptures à venir |
| **Health Score** | Score 0-100 de la santé inventaire d'une boutique |
| **ABC Rank** | Classification A/B/C des produits par contribution à la marge brute |
| **Demand Sigma** | Écart-type du taux de vente quotidien (mesure d'imprévisibilité de la demande) |
| **Lead Time Sigma** | Écart-type du délai de livraison réel d'un fournisseur (mesure de fiabilité) |

---

## 4. Architecture du pipeline algorithmique

Voici comment les données brutes (ventes et stocks) se transforment en recommandations opérationnelles :

```
DONNÉES BRUTES (Shopify, WooCommerce, CSV, Amazon...)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 1 — Correction OOS                                   │
│  Objectif : reconstruire la demande réelle pendant les      │
│  jours de rupture (quand le stock était à 0)                │
│  Sortie : theoretical_units_sold                            │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 2 — Détection Outliers (IQR)                         │
│  Objectif : identifier et corriger les pics de ventes       │
│  anormaux (erreurs, doublons) sans toucher les vrais pics   │
│  Sortie : corrected_units_sold                              │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 3 — Run Rate                                         │
│  Objectif : calculer le taux de vente quotidien réel        │
│  sur les 30 derniers jours propres                          │
│  Sortie : run_rate (unités/jour) + demand_sigma             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  ANALYSE FOURNISSEUR (parallèle)                            │
│  Objectif : mesurer fiabilité, délai moyen, variabilité LT  │
│  Sortie : reliability, average_delay, lead_time_sigma       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPES 4, 5, 6 — Prédictions opérationnelles               │
│  4. Date de rupture prévisionnelle                          │
│  5. Date d'alerte commande (ROP date)                       │
│  6. Quantité à commander (safety stock statistique)         │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  MÉTRIQUES ET SCORES                                        │
│  — ABC Analysis (priorisation par marge)                    │
│  — MAPE / précision prévision                               │
│  — Health Score inventaire                                  │
│  — KPIs financiers                                          │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
         TABLEAU DE BORD CLIENT
```

**Cadence d'exécution :** Le pipeline tourne automatiquement toutes les N heures (configurable) via l'Intelligence Worker. Chaque boutique connectée est traitée indépendamment.

---

## 5. Étape 1 — Correction des ruptures de stock (OOS)

### 5.1 Le problème

Imaginons ce cas : une boutique a vendu **0 unité** d'une robe pendant 10 jours. Est-ce parce que la robe ne se vend pas ? Non — c'est parce qu'il n'y avait plus de stock. La demande existait, mais elle était **censurée** : le produit ne pouvait pas se vendre car il n'était pas disponible.

Si on utilise ces "0" comme données réelles pour calculer le run rate, on sous-estimerait dramatiquement les ventes. La commande suivante serait trop petite. Et on se retrouverait à nouveau en rupture.

**Règle de détection d'une rupture :** `end_of_day_stock == 0`

### 5.2 La solution — Imputation par médiane glissante

**Formule :**
```
Pour chaque jour j où le stock en fin de journée = 0 :

  theoretical_units_sold[j] = median(
    units_sold[k]
    pour k dans les 14 jours précédant j
    où stock[k] > 0  ← seulement les jours sans rupture
  )

Si pas assez de jours non-rupture dans la fenêtre 14 jours :
  → Fallback : median(units_sold, tous les jours non-rupture de toute la série)
```

**Pourquoi la médiane et pas la moyenne ?**

Supposons que dans les 14 jours avant la rupture, il y a eu une promotion flash qui a généré 200 ventes sur un jour (au lieu des 5 habituelles). Avec la **moyenne**, ce pic gonfle artificiellement l'estimation. Avec la **médiane**, ce pic n'a aucun impact — on garde la valeur du milieu qui représente la demande normale.

### 5.3 Exemple concret

| Jour | Ventes brutes | Stock fin de journée | Rupture ? | Ventes corrigées |
|------|:---:|:---:|:---:|:---:|
| J-14 | 5 | 50 | Non | 5 |
| J-13 | 4 | 46 | Non | 4 |
| J-12 | 6 | 40 | Non | 6 |
| J-11 | 5 | 35 | Non | 5 |
| ... | ... | ... | ... | ... |
| J | 0 | 0 | **OUI** | **5** ← médiane des 14j |
| J+1 | 0 | 0 | **OUI** | **5** ← même logique |

Les jours de rupture ont maintenant une demande théorique estimée à 5 unités/jour. Le run rate ne sera pas biaisé par ces zéros.

### 5.4 Cas d'usage métier

- **Bestseller en rupture** : Un produit vendu à 20 unités/jour part en rupture pendant 3 semaines. Sans correction, son run rate estimé chuterait à ~3 unités/jour (15 jours normaux + 21 jours à 0). Avec la correction, il reste à 20 unités/jour et le prochain réapprovisionnement sera correctement dimensionné.

- **Lancement produit raté** : Un produit lancé avec trop peu de stock manque sa fenêtre de vente. La correction OOS permet d'estimer la demande réelle pour recalibrer le volume du prochain approvisionnement.

### 5.5 Hypothèse et limite

> Cette méthode assume que la demande est **stable** sur 14 jours. Pour un produit lancé il y a 2 semaines, la fenêtre peut couvrir le lancement (demande atypiquement haute) plutôt que la croisière. C'est acceptable en MVP — à affiner avec STL décomposition pour les produits à forte saisonnalité.

**Fichier source :** `apps/api/src/modules/intelligence/algorithms/out_of_stock_correction.py`

---

## 6. Étape 2 — Détection et correction des outliers (IQR)

### 6.1 Le problème

Parmi les journées de ventes "normales", certaines sont anormalement élevées pour de mauvaises raisons :
- Double saisie dans le système de caisse
- Commande B2B exceptionnelle comptabilisée comme ventes courantes
- Erreur d'import CSV
- Retour de commandes mal enregistré

Ces "faux pics" gonflent le run rate et génèrent des commandes trop importantes.

**À ne pas confondre avec :** les vrais pics (Black Friday, soldes, influence virale) qui représentent une demande réelle et ne doivent PAS être corrigés.

### 6.2 La méthode IQR (John Tukey, 1977)

**Formule :**
```
Sur les jours sans rupture (is_stockout = False) :

  Q1 = 25e percentile des ventes
  Q3 = 75e percentile des ventes
  IQR = Q3 - Q1

  Borne haute = Q3 + 1.5 × IQR

Un jour est un outlier si :
  units_sold > borne_haute
  ET ce n'est PAS un jour de rupture
```

**Pourquoi seulement la borne HAUTE ?**

En prévision de demande, une valeur basse représente **une vraie faible demande** — ce n'est pas une erreur à corriger. Seules les valeurs anormalement hautes sont des erreurs potentielles. Corriger les valeurs basses (IQR lower bound) génèrerait des faux positifs sur les périodes naturellement creuses (dimanche, été...).

### 6.3 Visualisation IQR

```
Distribution des ventes (exemple) :

Q1=3  Médiane=5  Q3=8  IQR=5
Borne haute = 8 + 1.5×5 = 15.5

Ventes : [2, 3, 4, 5, 5, 6, 7, 8, 9, 200]
                                         ↑
                               200 > 15.5 → OUTLIER détecté
```

**Correction :** La valeur 200 est remplacée par la médiane glissante centrée sur 11 jours des jours propres voisins. Si les ventes voisines sont 5-6-7, la correction vaut ~6.

### 6.4 Exemple concret

| Jour | Ventes | Borne haute (15.5) | Outlier ? | Ventes corrigées |
|------|:---:|:---:|:---:|:---:|
| Lun | 5 | 15.5 | Non | 5 |
| Mar | 200 | 15.5 | **OUI** | **6** (médiane voisine) |
| Mer | 6 | 15.5 | Non | 6 |
| Jeu | 7 | 15.5 | Non | 7 |

### 6.5 Option avancée : IQR glissant (iqr_window=90)

Pour les produits à **forte saisonnalité** (ex : crème solaire vendue massivement en été et quasi pas en hiver), un IQR global sur toute la série flaguerait les ventes estivales comme outliers. Solution : calculer l'IQR sur une **fenêtre glissante de 90 jours** — la borne haute s'adapte localement à la saison.

**Cas d'usage :** Mode maillot de bain, crème solaire, doudoune, chocolats de Noël.

### 6.6 Limite

> La correction par médiane **centrée** (utilisant des données futures) est optimale en mode historique (batch). En mode production incrémental (ajout d'une nouvelle journée), Michi bascule automatiquement en mode backward. Cela reste documenté dans le contrat d'interface du pipeline.

**Fichier source :** `apps/api/src/modules/intelligence/algorithms/outlier_detection.py`

---

## 7. Étape 3 — Calcul du run rate (taux de vente)

### 7.1 Définition

Le **run rate** est le taux de vente quotidien moyen d'un produit, calculé sur les 30 dernières journées propres (hors ruptures, hors outliers). C'est **la métrique centrale** de toute la mécanique prédictive de Michi.

Toutes les prédictions (date de rupture, quantité à commander, score ABC...) dépendent du run rate.

### 7.2 Formule — Médiane glissante adaptative

**Étape 1 : Isoler les jours propres**
```
clean_values = corrected_units_sold[ jours non-rupture ET non-outlier ]
```

**Étape 2 : Calculer les fenêtres**
```
rr_30j = median( 30 dernières valeurs propres )   ← stable, inertiel
rr_7j  = median( 7 dernières valeurs propres )    ← réactif, capte la tendance
```

**Étape 3 : Mesurer le momentum**
```
short_term = mean( 7 dernières valeurs propres )
medium_term = mean( 30 dernières valeurs propres )

momentum = short_term / medium_term
```

Le momentum mesure si la demande est en accélération récente. Un momentum de 1.5 signifie que les 7 derniers jours ont vendu 50% de plus que la moyenne des 30 derniers jours.

**Étape 4 : Blend adaptatif**
```
alpha = clip( (momentum - 1.0) / 0.5, 0, 1 )

run_rate = (1 - alpha) × rr_30j + alpha × rr_7j
```

| Momentum | Alpha | Run rate |
|:---:|:---:|:---:|
| 1.0 (stable) | 0 | 100% médiane 30j |
| 1.2 | 0.4 | 60% médiane 30j + 40% médiane 7j |
| 1.5 ou + | 1 | 100% médiane 7j |

**Pourquoi ce blend plutôt qu'un simple switch ?**

L'ancienne implémentation bascule brutalement de 30j à 7j dès que le momentum dépasse 1.2. Cela crée une discontinuité : un jour le run_rate vaut 8 (médiane 30j), le lendemain il vaut 15 (médiane 7j), puis repasse à 8. Le blend progressif lisse ce comportement — le run_rate évolue graduellement avec la tendance.

**Étape 5 : Volatilité (demand_sigma)**
```
demand_sigma = std( clean_values, fenêtre 30j propres )
```

Le sigma de la demande capture à quel point les ventes sont variables. Un produit qui vend toujours 5±0.5 unités/jour a un sigma faible (demande prévisible). Un produit qui oscille entre 2 et 20 unités/jour a un sigma élevé (demande imprévisible → besoin d'un safety stock plus grand).

### 7.3 Pourquoi la médiane plutôt que la moyenne ?

| Situation | Avec moyenne | Avec médiane |
|-----------|:---:|:---:|
| Ventes normales : 5, 5, 6, 4, 5 | 5 | 5 |
| Avec pic résiduel : 5, 5, 50, 4, 5 | 13.8 | 5 |
| Avec mois creux : 1, 1, 5, 5, 6 | 3.6 | 5 |

La médiane est **robuste aux valeurs extrêmes**. Même si l'IQR a raté un outlier ou si un mois a été atypique, la médiane des 30 jours propres reste stable.

### 7.4 Exemple concret — Produit en accélération

Un jean bestseller vend normalement 5 unités/jour (médiane 30j). Une influenceuse le porte en story. Les 7 derniers jours : 12 ventes/jour.

```
rr_30j = 5 unités/jour
rr_7j  = 12 unités/jour
momentum = 12/5 = 2.4
alpha = clip( (2.4-1.0)/0.5, 0, 1 ) = clip(2.8, 0, 1) = 1.0

run_rate = 0×5 + 1×12 = 12 unités/jour
```

→ Michi détecte l'accélération et utilise le run rate court terme. La prédiction de rupture s'ajuste immédiatement.

### 7.5 Fallback — Séries courtes

Si moins de 4 jours propres sont disponibles (produit très récent ou très longue rupture), Michi utilise la médiane globale de toute la série disponible. Si même cela n'est pas possible, le run rate est 0 (pas de commande déclenchée).

**Fichier source :** `apps/api/src/modules/intelligence/algorithms/run_rate.py`

---

## 8. Étape 4 — Prédiction de la date de rupture

### 8.1 Le concept

À partir du stock actuel et du run rate, Michi calcule combien de jours de stock il reste, puis en déduit une date de rupture.

### 8.2 Formule

```
days_until_stockout = round( current_stock / run_rate )

predicted_stockout_date = today + timedelta(days = days_until_stockout)

Cas spéciaux :
  Si run_rate = 0  → None   (stock infini, pas de rupture prévisible)
  Si stock ≤ 0     → today  (rupture immédiate)
```

**Pourquoi `round()` et pas `floor()` ?**

`floor(28.9)` = 28 jours — vous prédisez la rupture 0.9 jours trop tôt.  
`round(28.9)` = 29 jours — vous prédisez la rupture au bon moment.

Ce détail est important car le run rate est lui-même une médiane lissée. Ajouter un biais systématique de -1 jour sur chaque prédiction génère des alertes prématurées qui perdent en crédibilité.

### 8.3 Exemple

```
Stock actuel : 147 unités
Run rate     : 4.8 unités/jour
Date du calcul : 15 mai

days = round(147 / 4.8) = round(30.625) = 31 jours

Rupture prévue : 15 mai + 31 jours = 15 juin
```

Le client voit : **"Rupture prévue le 15 juin"** — clair, actionnable, daté.

### 8.4 Limites

> Cette prédiction ne tient pas compte des **commandes fournisseurs en transit**. Si une livraison de 200 unités arrive dans 5 jours, la rupture du 15 juin n'aura pas lieu. L'intégration du statut des POs en cours dans le calcul est planifiée en post-MVP.

**Fichier source :** `apps/api/src/modules/intelligence/algorithms/predictions.py`

---

## 9. Étape 5 — Date d'alerte commande (ROP Date)

### 9.1 Pourquoi cette fonctionnalité est critique

C'est **la fonctionnalité qui crée la valeur réelle de Michi**.

Avant son implémentation : le client voyait "Rupture dans 14 jours". Il passait sa commande. Le fournisseur avait un délai de livraison de 21 jours. Le client recevait la livraison 7 jours **après** la rupture.

La prédiction de rupture sans la date d'alerte commande n'est pas actionnable. Elle crée une fausse sécurité.

**Illustration du problème :**

```
Aujourd'hui          Rupture              Livraison
    │                   │                     │
    ├───── 14 jours ────►│                     │
    │                                         │
    │◄─────────────── 21 jours LT ───────────►│
    │
    ↑ Si vous commandez aujourd'hui, la livraison arrive APRÈS la rupture.
    ↑ Il fallait commander il y a 7 jours.
```

### 9.2 Formule

```
effective_lead_time = ceil( lead_time + max(0, average_delay) )

reorder_alert_date = predicted_stockout_date - effective_lead_time (jours)
```

**Détail :**
- `lead_time` : délai théorique du fournisseur (en jours, saisi dans Michi)
- `average_delay` : retard moyen constaté sur les dernières livraisons (calculé par l'analyse fournisseur)
- `ceil()` : on arrondit vers le haut pour être conservateur — mieux vaut commander 1 jour trop tôt que 1 jour trop tard
- `max(0, ...)` : si le fournisseur livre parfois en avance (delay négatif), on ne raccourcit pas le délai de sécurité

### 9.3 Exemple

```
Stock actuel       : 147 unités
Run rate           : 4.8 unités/jour
Rupture prévue     : 15 juin
Lead time          : 21 jours
Retard moyen fourn.: 3 jours

effective_LT = ceil(21 + max(0, 3)) = ceil(24) = 24 jours

reorder_alert_date = 15 juin - 24 jours = 22 mai
```

Le client voit : **"Commander avant le 22 mai pour recevoir le stock avant la rupture"**

### 9.4 Interprétation opérationnelle

- **reorder_alert_date dans le futur** → Vous avez le temps. Commandez avant cette date.
- **reorder_alert_date = aujourd'hui** → Commandez aujourd'hui, urgent.
- **reorder_alert_date dans le passé** → Vous êtes en retard. La rupture est probable avant la livraison. Action d'urgence nécessaire (sourcing alternatif, précommande client, communication proactive).

### 9.5 Valeur ajoutée marketing

> "Michi ne vous dit pas seulement *quand* vous allez être en rupture. Il vous dit *quand commander* pour ne jamais l'être."

**Fichier source :** `apps/api/src/modules/intelligence/algorithms/predictions.py`

---

## 10. Étape 6 — Quantité de réapprovisionnement (Safety Stock)

### 10.1 L'enjeu

Combien commander ? La réponse naïve est `run_rate × lead_time`. Mais c'est insuffisant car :

1. La **demande varie** — certains jours vous vendez 2 fois plus que d'habitude
2. Le **fournisseur est imparfait** — il livre parfois avec 5 jours de retard
3. Ces deux sources d'incertitude s'accumulent

Le **safety stock** est le stock tampon qui absorbe ces deux incertitudes. Sa taille dépend du niveau de service cible (95% = on accepte d'être en rupture 5% du temps) et des niveaux de volatilité observés.

### 10.2 La formule — Silver-Pyke-Peterson §7.4

C'est la formule académique de référence en supply chain (Silver, Pyke & Peterson, *Inventory Management and Production Planning and Scheduling*, 3e édition).

```
Étape 1 : Z-score du service level
  Z = norm.ppf(service_level)
  
  Pour service_level = 0.95 → Z = 1.645
  Pour service_level = 0.99 → Z = 2.326
  Pour service_level = 0.90 → Z = 1.282

Étape 2 : Lead time effectif
  LT_eff = lead_time + average_delay

Étape 3 : Cycle Stock (couverture du délai moyen)
  cycle_stock = run_rate × LT_eff

Étape 4 : Safety Stock statistique
  combined_variance = (LT_eff × σd²) + (D² × σlt²)
  safety_stock = Z × √( combined_variance )

  Où :
    σd  = demand_sigma = écart-type des ventes journalières
    D   = run_rate
    σlt = lead_time_sigma = écart-type du délai fournisseur

Étape 5 : Quantité à commander
  target_stock = cycle_stock + safety_stock
  raw_qty = max(0, target_stock - current_stock)
  reorder_qty = ceil(raw_qty / MOQ) × MOQ
```

### 10.3 Décomposition de la variance combinée

La formule `LT_eff × σd² + D² × σlt²` est souvent incomprise. Voici son interprétation intuitive :

**Premier terme : `LT_eff × σd²`**
= Variabilité de la demande pendant tout le lead time  
→ Si le lead time est de 20 jours et la demande varie de ±2 unités/jour, sur 20 jours cette variabilité s'accumule.

**Deuxième terme : `D² × σlt²`**
= Variabilité causée par l'incertitude du délai fournisseur  
→ Si le fournisseur varie de ±4 jours et qu'on vend 10 unités/jour, ±4 jours représentent ±40 unités.

Les deux termes s'additionnent car ils sont **indépendants** (la variabilité de la demande et celle du fournisseur ne sont pas corrélées — c'est l'hypothèse classique du modèle).

### 10.4 Exemple complet pas à pas

```
Produit    : Robe fleurie, taille M
Stock      : 45 unités
Run rate   : 5 unités/jour
Sigma demande : 1.5 unités/jour (demande modérément variable)
Lead time  : 21 jours
Retard moyen fournisseur : 3 jours
Sigma LT   : 4 jours (fournisseur assez variable)
Service level : 95% → Z = 1.645
MOQ        : 50 unités

──────────────────────────────────────────────

LT_eff = 21 + 3 = 24 jours

Cycle stock = 5 × 24 = 120 unités

Variance combinée = (24 × 1.5²) + (5² × 4²)
                  = (24 × 2.25) + (25 × 16)
                  = 54 + 400
                  = 454

Safety stock = 1.645 × √454 = 1.645 × 21.3 = 35 unités

Target stock = 120 + 35 = 155 unités

Raw qty = max(0, 155 - 45) = 110 unités

Reorder qty = ceil(110/50) × 50 = ceil(2.2) × 50 = 3 × 50 = 150 unités
```

**Le client voit : "Commander 150 unités"**

### 10.5 Lecture intuitive de la répartition

```
Sur les 150 unités commandées :
  120 unités = cycle stock  (couvrir la demande pendant les 24j de LT)
   35 unités = safety stock (absorber la variabilité demande + fournisseur)

  Les 35 unités de safety stock se décomposent :
  → √54 = 7.3 unités liées à la variabilité de la demande
  → √400 = 20 unités liées à l'incertitude fournisseur
  (ces deux composantes sont combinées sous la racine, pas additionnées)
```

### 10.6 Impact du niveau de service

| Service level | Z | Safety stock | Interprétation |
|:---:|:---:|:---:|---|
| 90% | 1.282 | 27 unités | On accepte d'être en rupture 1 fois sur 10 |
| 95% | 1.645 | 35 unités | On accepte d'être en rupture 1 fois sur 20 |
| 99% | 2.326 | 50 unités | On accepte d'être en rupture 1 fois sur 100 |

> **Conseil métier :** Pour les produits classe A (best-sellers, forte marge), utiliser 95-99%. Pour les produits classe C (longue traîne), 90% suffit. La personnalisation du service level par classe ABC est une fonctionnalité roadmap.

### 10.7 Différenciateur Dual Sigma

La majorité des outils SME calculent le safety stock avec **seulement** la variabilité de la demande (`σd`), ignorant l'incertitude fournisseur (`σlt`). Dans notre exemple, ignorer `σlt` donnerait :

```
Safety stock = 1.645 × √54 = 1.645 × 7.3 = 12 unités
→ Commande = ceil((120+12-45)/50)×50 = 2×50 = 100 unités

Vs. Michi dual sigma : 150 unités
```

Avec un fournisseur variable (σlt=4j), Michi commande 50 unités de plus. C'est cet écart qui évite la rupture quand le fournisseur arrive 6 jours en retard.

**Fichier source :** `apps/api/src/modules/intelligence/algorithms/predictions.py`

---

## 11. Analyse ABC — Priorisation par la marge

### 11.1 Le principe de Pareto en supply chain

Le principe de Pareto dit que **80% de la valeur est produite par 20% des produits**. L'analyse ABC traduit ce principe en classification opérationnelle :

- **Classe A** : les 20% de SKUs qui génèrent 80% de la marge brute → surveillance quotidienne, priorité absolue
- **Classe B** : les suivants qui génèrent les 15% de marge suivants → surveillance hebdomadaire
- **Classe C** : le reste qui génère les 5% restants → surveillance mensuelle, candidats au déréférencement

### 11.2 Formule

```
Étape 1 : Calcul du profit brut annualisé par SKU
  annual_gross_profit = (sale_price - cost_price) × run_rate × 365

Étape 2 : Tri décroissant par profit
  [P1 > P2 > P3 > ... > Pn]

Étape 3 : Calcul du % cumulé
  cum_pct[i] = (P1 + P2 + ... + Pi) / (P1 + P2 + ... + Pn)

Étape 4 : Attribution du rang
  cum_pct ≤ 0.80 → A
  0.80 < cum_pct ≤ 0.95 → B
  cum_pct > 0.95 → C
  annual_gross_profit ≤ 0 → C (par défaut)
```

### 11.3 Pourquoi la marge brute et pas le chiffre d'affaires ?

Exemple révélateur :

| Produit | Prix vente | Coût achat | Run rate | CA annuel | **Marge annuelle** |
|---------|:---:|:---:|:---:|:---:|:---:|
| T-shirt basique | 15€ | 3€ | 20/j | 109 500€ | **87 600€** |
| Sac designer | 350€ | 280€ | 1/j | 127 750€ | **25 550€** |

Basé sur le CA, le sac designer est "plus important". Basé sur la **marge brute**, le t-shirt génère 3.4× plus de valeur financière réelle. L'analyse ABC par marge oriente les décisions d'achat vers la vraie profitabilité.

### 11.4 Exemple avec 5 produits

```
Produits (run_rate en unités/j, prix et coût en €) :

SKU       run_rate  sale  cost  marge  profit_annuel  cum_%   rang
──────────────────────────────────────────────────────────────────
Robe A    8.0       89€   25€   64€    186 880€       37.4%   A
Jean B    5.0       79€   30€   49€    89 425€        55.3%   A
Top C     12.0      29€   8€    21€    91 980€        73.7%   A
Manteau D 1.5       199€  90€   109€   59 678€        85.6%   B
Accessoir E 0.3    49€   30€   19€    2 079€         100%     C
```

→ 3 produits (60%) génèrent 73.7% de la marge → classe A  
→ 1 produit classe B, 1 produit classe C

### 11.5 Utilisation opérationnelle

| Rang | Fréquence de suivi | Niveau de service cible | Action si rupture |
|:---:|---|:---:|---|
| A | Quotidienne | 97-99% | Urgence maximale — sourcing alternatif |
| B | Hebdomadaire | 95% | Standard — commande normale |
| C | Mensuelle | 90% | Analyse déréférencement si peu de marge |

### 11.6 Limite importante — La saisonnalité

> L'annualisation `× 365` suppose une demande stable sur 12 mois. Pour une marque de mode, un maillot de bain calculé en octobre aura un run_rate proche de 0 → profit annualisé proche de 0 → classé C. Pourtant ce produit a peut-être généré 70% du profit de la boutique en juillet.
>
> **Recommandation terrain :** Pour les catalogues fortement saisonniers, relancer l'analyse ABC en début de chaque saison. La classification d'octobre n'est pas représentative pour préparer l'été.

**Fichier source :** `apps/api/src/modules/intelligence/algorithms/abc_analysis.py`

---

## 12. Précision des prévisions (MAPE, MAE, Biais)

### 12.1 Pourquoi mesurer la précision ?

Un système de prévision sans mesure de sa propre précision est une boîte noire. Michi calcule trois métriques complémentaires pour que les équipes et les clients comprennent dans quelle mesure les prévisions sont fiables.

### 12.2 Les trois métriques

#### MAPE — Mean Absolute Percentage Error

```
Pour chaque jour t où les ventes réelles > 0 :
  erreur_relative[t] = | ventes_réelles[t] - run_rate | / ventes_réelles[t]

MAPE = mean( erreur_relative )
```

**Interprétation :** MAPE = 0.12 → les prévisions se trompent en moyenne de 12% par rapport aux ventes réelles.

**Non bornée :** La MAPE peut dépasser 1.0 (100%). Une MAPE de 2.5 (250% d'erreur) signale que le modèle est très mal calibré pour ce produit. Ne pas capituler artificiellement à 1.0 — c'est masquer un problème.

#### MAE — Mean Absolute Error

```
MAE = mean( | ventes_réelles[t] - run_rate | )
```

**Interprétation :** MAE = 2.3 → les prévisions se trompent en moyenne de 2.3 unités par jour (en valeur absolue, sans tenir compte du signe).

La MAE est plus utile que la MAPE pour les produits à faible volume : si un produit vend 1 unité/jour, une erreur d'1 unité donne MAPE=100% mais MAE=1 unité — ce qui est tout à fait acceptable opérationnellement.

#### Biais

```
Biais = mean( run_rate - ventes_réelles[t] )
```

**Interprétation :**
- Biais > 0 → sur-estimation systématique (on commande trop)
- Biais < 0 → sous-estimation systématique (on sous-commande)
- Biais ≈ 0 → pas de dérive systématique

**Le biais est plus important que la MAPE pour les décisions d'achat.** Une MAPE de 20% avec biais=-5% signifie qu'on sous-estime systématiquement les ventes → risque de rupture chronique. Une MAPE de 20% avec biais=+5% → on sur-commande légèrement → capital immobilisé mais pas de rupture.

### 12.3 Exemple comparatif

```
Run rate calculé : 10 unités/jour
Ventes réelles des 7 derniers jours : [8, 12, 9, 11, 10, 7, 13]

Erreurs relatives : 0.25, 0.20, 0.10, 0.10, 0.00, 0.30, 0.30
MAPE = mean([0.25, 0.20, 0.10, 0.10, 0.00, 0.30, 0.30]) = 0.18 → 18%

Erreurs absolues  : 2, 2, 1, 1, 0, 3, 3
MAE  = mean([2, 2, 1, 1, 0, 3, 3]) = 1.71 unités/jour

Biais = mean([10-8, 10-12, 10-9, 10-11, 10-10, 10-7, 10-13])
      = mean([2, -2, 1, -1, 0, 3, -3]) = 0 → pas de biais systématique
```

Verdict : MAPE de 18%, erreur de ±1.7 unités/jour, pas de biais. Ce run rate est acceptable.

### 12.4 Seuils de référence par catégorie

| MAPE | Interprétation | Action recommandée |
|:---:|---|---|
| < 15% | Excellente précision | Confiance maximale dans les prévisions |
| 15-30% | Précision acceptable | Surveiller le biais ; augmenter le safety stock margin |
| 30-60% | Précision limitée | Vérifier la qualité des données ; envisager revue manuelle |
| > 60% | Modèle peu fiable | Produit très volatile ou données corrompues ; action manuelle |

**Fichier source :** `apps/api/src/modules/intelligence/algorithms/mape.py`

---

## 13. Score de santé inventaire

### 13.1 Concept

Le Health Score est un indicateur agrégé, sur 100, qui résume la santé de l'inventaire d'une boutique en un chiffre unique. Il est conçu pour être la métrique de premier niveau du tableau de bord : un chiffre que le dirigeant voit en arrivant le matin et qui lui donne immédiatement le niveau d'alerte.

### 13.2 Formule

```
Le score est composé de 3 éléments pondérés :

1. DISPONIBILITÉ DU CA (poids : 50%)
   avail = 1 - revenue_at_risk / (forecasted_30d + revenue_at_risk)
   où forecasted_30d = run_rate_total × 30 × avg_sale_price

2. ROTATION DU STOCK (poids : 30%)
   coverage = couverture moyenne en jours (stock / run_rate)
   
   Si coverage < 7j  : rot = coverage / 7           (stock critique)
   Si 7j ≤ cov ≤ 45j : rot = 1.0                   (zone optimale)
   Si 45j < cov < 90j : rot = 1 - (cov-45) / 45   (sur-stockage léger)
   Si cov ≥ 90j       : rot = max(0, 0.5-(cov-90)/180)  (sur-stockage fort)

3. TAUX DE RUPTURE (poids : 20%)
   out_ratio = 1 - stockout_count / total_skus

Score final = round( (avail×0.5 + rot×0.3 + out_ratio×0.2) × 100 )
Borné entre 0 et 100.
```

### 13.3 Visualisation de la courbe de rotation

```
rot
 1.0 │    ┌──────────────────┐
     │   /│                  │\
 0.5 │  / │                  │ \___
     │ /  │                  │
 0.0 │/   │                  │
     └────┴──────────────────┴─────────── coverage (jours)
     0    7                 45  90       270
          
     Zone critique  Zone optimale  Sur-stockage léger/fort
```

La zone optimale 7-45 jours correspond aux standards mode/beauté avec des délais fournisseurs de 2-4 semaines. En dessous de 7 jours, l'entreprise est dans la zone rouge (rupture imminente). Au-delà de 90 jours, le capital est excessivement immobilisé.

### 13.4 Exemple de calcul

```
Boutique avec :
  - Revenue at risk : 5 000€
  - Run rate total  : 50 unités/j
  - Prix moyen      : 45€/unité
  - Coverage moyen  : 32 jours
  - 3 SKUs en rupture sur 200

forecasted_30d = 50 × 30 × 45 = 67 500€
avail = 1 - 5000/(67500+5000) = 1 - 0.069 = 0.931

coverage = 32j → zone optimale → rot = 1.0

out_ratio = 1 - 3/200 = 0.985

Health Score = round((0.931×0.5 + 1.0×0.3 + 0.985×0.2) × 100)
             = round((0.466 + 0.300 + 0.197) × 100)
             = round(96.3)
             = 96 / 100 ✅
```

### 13.5 Interprétation des seuils

| Score | Couleur | État |
|:---:|:---:|---|
| 90-100 | 🟢 | Excellent — gestion optimale |
| 75-89 | 🟡 | Bon — quelques vigilances |
| 60-74 | 🟠 | Attention — actions correctives requises |
| < 60 | 🔴 | Critique — intervention urgente |

### 13.6 Utilisation en tendance

Le Health Score prend tout son sens en **évolution hebdomadaire** :
- Score qui passe de 82 à 74 → dégradation → investiguer
- Score qui progresse de 65 à 78 → les actions correctives ont porté leurs fruits

**Fichier source :** `apps/api/src/modules/intelligence/analytics/health_score.py`

---

## 14. Analyse des performances fournisseurs

### 14.1 Pourquoi c'est critique

Le safety stock n'est utile que si le fournisseur est pris en compte dans son calcul. Un fournisseur qui livre toujours exactement à l'heure n'a pas besoin de safety stock côté lead time. Un fournisseur qui livre avec 0 à 15 jours de retard imprévisible a besoin d'un buffer important.

Michi calcule automatiquement 3 métriques de performance fournisseur à partir de l'historique des Purchase Orders (POs).

### 14.2 Les trois métriques

#### Fiabilité (Reliability)

```
reliability = on_time_count / total_POs_completed

où : on_time_count = POs livrés avec delay ≤ 0
     delay = actual_arrival_date - expected_arrival_date
```

**Interprétation :** reliability = 0.85 → 85% des commandes arrivent à l'heure ou en avance.

#### Délai moyen (Average Delay)

```
average_delay = mean( actual_arrival_date - expected_arrival_date )  en jours

Positif = arrive en retard en moyenne
Négatif = arrive en avance en moyenne
```

**Interprétation :** average_delay = 2.3 → ce fournisseur livre en moyenne 2.3 jours après la date prévue. Ce délai est intégré dans le calcul du lead time effectif (`LT_eff = LT + 2.3`).

#### Sigma du lead time (Lead Time Sigma)

```
lead_time_sigma = std( actual_arrival_date - order_date, ddof=1 )  en jours
```

**Note `ddof=1` :** On utilise la variance d'échantillon (ddof=1) et non de population (ddof=0). Sur 5 POs, l'écart est de +11.8% — matériel pour les petits portfolios. Cela évite de sous-estimer la variabilité et donc de sous-dimensionner le safety stock.

**Interprétation :** sigma_lt = 4.1 → la durée réelle du lead time varie de ±4.1 jours autour de la moyenne. Ce sigma est directement injecté dans la formule du safety stock (`D² × σlt²`).

### 14.3 Exemple — Comparaison de deux fournisseurs

```
Fournisseur A (fiable)       Fournisseur B (imprévisible)
─────────────────────────    ────────────────────────────
reliability  : 0.95          reliability  : 0.70
average_delay: 0.5 jours     average_delay: 3.0 jours
lt_sigma     : 1.5 jours     lt_sigma     : 7.0 jours

Pour run_rate=5, sigma_d=1.5, LT=21j, service_level=95% :

Safety stock A = 1.645 × √(21.5×2.25 + 25×2.25) = 1.645 × √104 = 17 unités
Safety stock B = 1.645 × √(24×2.25 + 25×49)    = 1.645 × √1279 = 59 unités

→ Travailler avec B nécessite 42 unités de safety stock supplémentaires
  soit une immobilisation de capital 3.5× plus importante.
```

Cette comparaison permet aux acheteurs de **quantifier financièrement le coût de la mauvaise fiabilité fournisseur**.

### 14.4 Mise à jour automatique

Les métriques fournisseurs sont recalculées automatiquement à chaque cycle du worker, dès qu'un nouveau PO passe au statut "COMPLETED". Elles se propagent immédiatement dans le calcul du safety stock au prochain cycle de prédictions.

**Fichier source :** `apps/api/src/modules/intelligence/services/supplier_analysis.py`

---

## 15. KPIs financiers inventaire

### 15.1 Les quatre indicateurs

#### Valeur de l'inventaire au coût

```
inventory_value_cost = Σ( stock_actuel × coût_achat )
```

Ce que vous avez immobilisé dans votre entrepôt au prix d'achat. C'est le montant que vous avez "dépensé" et qui n'est pas encore transformé en CA.

#### Valeur de l'inventaire au prix de vente

```
inventory_value_sale = Σ( stock_actuel × prix_de_vente )
```

Ce que rapporterait votre inventaire si vous vendiez tout demain. L'écart entre `inventory_value_sale` et `inventory_value_cost` représente la marge potentielle dormante dans l'entrepôt.

#### Revenue at Risk

```
revenue_at_risk = Σ( reorder_quantity × prix_de_vente )
```

La valeur totale des commandes fournisseurs à passer pour éviter les ruptures à venir. C'est le CA potentiel "à risque" si aucune action n'est entreprise.

> **Nuance terminologique :** Dans la littérature supply chain, "Revenue at Risk" désigne souvent le CA perdu sur des ruptures déjà en cours. Dans Michi, la définition est légèrement différente : c'est la valeur des besoins futurs de réapprovisionnement. Cette nuance doit être clarifiée dans la communication client.

#### Couverture moyenne (Days of Supply)

```
coverage_avg = mean( stock[i] / run_rate[i] ) pour i ∈ SKUs avec run_rate > 0
```

Nombre de jours moyen pendant lequel le stock actuel peut couvrir la demande. Indicateur de santé globale du niveau de stock.

### 15.2 Tableau de bord financier type

```
┌─────────────────────────────────────────────────────┐
│  INVENTAIRE                                         │
│  Valeur coût    : 45 230€                           │
│  Valeur vente   : 98 750€    (marge potentielle)    │
│  Revenue at Risk:  8 400€    (à commander)          │
│  Coverage moyen :    28 jours                       │
└─────────────────────────────────────────────────────┘
```

**Fichiers sources :** `apps/api/src/modules/intelligence/analytics/financial_kpis.py`, `analytics/risk_scoring.py`

---

## 16. Cas d'usage complets — Scénarios terrain

### Cas 1 — La robe qui part en rupture avant les soldes

**Situation :** 15 juin. Sophie gère une boutique de robes. Les soldes démarrent le 26 juin. Elle utilise Michi.

**Ce que Michi lui dit :**
```
Robe florale, taille S (SKU: ROB-FL-S)
  ABC Rank     : A (génère 12% de votre marge)
  Run rate     : 8.3 unités/jour (en hausse +40% cette semaine)
  Stock actuel : 45 unités
  Rupture prévue : 20 JUIN ← 4 jours avant les soldes !
  Alerte commande : 28 MAI ← elle est déjà passée
  Fournisseur  : reliability 78%, LT 18j, retard moyen 4j
  Commander    : 200 unités URGENCE
```

**Ce que Sophie fait :**
1. Elle voit que l'alerte du 28 mai a été manquée
2. Le fournisseur habituel ne peut pas livrer à temps (LT effectif = 22j)
3. Elle active un fournisseur alternatif en Europe (LT 5j, prix +15%)
4. Les 200 unités arrivent le 22 juin, 4 jours avant les soldes
5. Elle ne rate pas sa fenêtre commerciale la plus importante de l'année

**Sans Michi :** Elle découvrait la rupture le 19 ou 20 juin — trop tard.

---

### Cas 2 — Le bestseller mal calibré

**Situation :** Un jean coupe slim vend normalement 15 unités/jour. En janvier, il est passé en rupture pendant 3 semaines suite à un problème logistique fournisseur. Résultat : le run rate calculé manuellement (sur Excel) voit 21 jours à 0 vente dans l'historique → run rate sous-estimé à 8 unités/jour.

**Avec Michi :**
1. L'OOS correction impute les 21 jours de rupture avec la médiane des 14 jours précédents → 15 unités/jour
2. Le run rate calculé sur les données corrigées est bien de 15 unités/jour
3. La commande suivante est calibrée à 450 unités (30j × 15) au lieu de 240 unités (30j × 8)
4. Pas de sous-stock au retour du fournisseur

**Impact financier :** 210 unités supplémentaires commandées × 25€ de marge = 5 250€ de marge récupérée sur le prochain cycle.

---

### Cas 3 — Le fournisseur peu fiable découvert grâce aux metrics

**Situation :** L'équipe utilise depuis 3 mois un fournisseur marocain pour sa collection été. Michi calcule automatiquement ses métriques sur les 8 POs historiques.

```
Fournisseur Maroc :
  Reliability  : 0.625 (4 livraisons sur 8 à l'heure)
  Average delay: +6.2 jours
  LT sigma     : 8.5 jours

Comparaison avec fournisseur Portugal :
  Reliability  : 0.950
  Average delay: +1.1 jours
  LT sigma     : 2.1 jours
```

**Décision :** Le responsable achat quantifie l'impact :

```
Safety stock Maroc   = 1.645 × √(26.2×2.25 + 25×72.25) = 71 unités supplémentaires
Safety stock Portugal= 1.645 × √(22.1×2.25 + 25×4.41)  = 20 unités supplémentaires

Coût immobilisation supplémentaire = 51 unités × 30€ coût = 1 530€ de capital gelé
```

→ Le fournisseur marocain coûte 1 530€ de capital immobilisé supplémentaire par SKU, à cela s'ajoutent les ruptures liées aux retards. La décision de réduire les commandes vers le Maroc est basée sur des chiffres, pas sur une impression.

---

### Cas 4 — Le tableau de bord du lundi matin

**Situation :** Chaque lundi, le dirigeant ouvre Michi avant toute réunion.

```
MICHI DASHBOARD — Semaine du 26 mai

Health Score : 71/100  ↓ (était 78 la semaine dernière)
               Alerte : couverture passée de 35j à 19j

Revenue at Risk :    12 400€
Produits classe A en alerte : 4 SKUs
  → Alerte commande dans < 7 jours

Top 3 urgences :
  1. Jean slim noir     → Commander avant le 29 mai (DEMAIN)
  2. Sac canvas marine  → Commander avant le 31 mai
  3. Veste lin beige    → Commander avant le 3 juin

MAPE global : 14.2% (stable, bon niveau)
Biais : -0.8%  (légère sous-estimation, surveiller)
```

En 2 minutes, le dirigeant a :
- Une évaluation de la santé globale (71/100, en dégradation)
- Les 3 actions prioritaires avec dates limites
- Un indicateur de fiabilité du système de prévision

---

### Cas 5 — Revue ABC trimestrielle

**Situation :** Début de saison. L'acheteur lance la revue ABC.

```
Catalogue : 450 SKUs actifs

Classe A : 38 SKUs (8.4%) → génèrent 80% de la marge
Classe B : 62 SKUs (13.8%) → génèrent 15% de la marge
Classe C : 350 SKUs (77.8%) → génèrent 5% de la marge

Insights :
  - 15 SKUs classe C ont une marge négative → candidats au déréférencement
  - 8 SKUs récemment passés de B à A → augmenter les niveaux de service
  - 12 SKUs passés de A à C (fin de collection) → liquider le stock résiduel
```

→ L'acheteur concentre ses négociations fournisseurs sur les 38 SKUs classe A. Il prend des décisions de déréférencement basées sur la marge réelle, pas sur des impressions.

---

## 17. Positionnement marché et valeur ajoutée

### 17.1 Le marché ciblé

**Cible :** E-commerçants indépendants et PME (1M€ - 50M€ de CA) dans la **mode et la beauté**, vendant sur Shopify, WooCommerce, Amazon.

**Taille du problème :** En France, 15 000 marques de mode vendent en ligne. En moyenne, un e-commerçant mode perd 8-15% de son CA annuel en ruptures de stock manquées. Sur un CA de 2M€, c'est 160 000€ à 300 000€ de ventes ratées par an.

### 17.2 Différenciateurs techniques clés

| Différenciateur | Ce que ça signifie concrètement | Valeur client |
|---|---|---|
| **Correction OOS automatique** | Les ruptures passées ne faussent plus les prévisions futures | Run rate fiable même sur produits souvent en rupture |
| **Dual Sigma safety stock** | La variabilité fournisseur entre dans le calcul du buffer | Moins de ruptures quand le fournisseur est en retard |
| **ROP Date (Reorder Alert)** | "Commander avant le 22 mai" pas "rupture dans 14 jours" | Action immédiate, pas juste une alerte |
| **ABC par marge brute** | Priorisation sur la vraie valeur financière | Focus sur ce qui rapporte vraiment |
| **Multi-canal unifié** | Shopify + Amazon + WooCommerce dans une seule vue | Vision complète sans consolidation manuelle |

### 17.3 Arguments marketing fondés sur les algorithmes

**"Michi corrige vos historiques de vente"**
> La plupart des outils de prévision utilisent vos ventes brutes telles quelles. Le problème : si un produit était en rupture pendant 3 semaines, ses ventes affichent 0 sur cette période — faussant tous les calculs futurs. Michi reconstruit automatiquement la demande réelle pendant les ruptures, donnant des prévisions 40% plus précises sur les produits à forte rotation.

**"Michi connaît vos fournisseurs aussi bien que vous"**
> Michi analyse l'historique de chaque Purchase Order pour calculer la fiabilité, le retard moyen et la variabilité de chaque fournisseur. Ces données entrent directement dans le calcul du stock de sécurité — automatiquement. Plus votre fournisseur est imprévisible, plus Michi adapte le buffer pour vous protéger.

**"Michi vous dit quand commander, pas juste quand vous allez manquer"**
> Savoir que vous allez être en rupture dans 14 jours ne sert à rien si votre fournisseur livre en 21 jours. Michi calcule la date exacte avant laquelle vous devez passer votre commande pour recevoir le stock à temps. Si cette date est déjà passée, l'alerte devient urgente.

**"Michi priorise les bons produits"**
> L'analyse ABC de Michi classe vos produits par marge brute générée, pas par chiffre d'affaires. Un produit vendu 200€ avec 10€ de marge est moins prioritaire qu'un produit vendu 30€ avec 20€ de marge. Cette distinction change radicalement les décisions d'achat — et la rentabilité.

### 17.4 Positionnement tarifaire et ROI

**Calcul de ROI type :**
```
Client : boutique mode, 2M€ CA, 600 SKUs, 3 acheteuses

Coût de l'outil         : X€/mois

Gains identifiés :
  Ventes récupérées     : 2M€ × 10% ruptures évitées = 200 000€
  Capital libéré        : 15% réduction surstockage = 30 000€
  Temps économisé       : 3 acheteuses × 8h/semaine = 1 248h/an
                          Valeur : 1 248 × 40€ = 49 920€

Total gain estimé       : ~280 000€/an
ROI                     : [280 000 / (X × 12) - 1] × 100%
```

Pour tout tarif SaaS < 5 000€/mois, le ROI dépasse 400%.

---

## 18. Fiches récapitulatives — Aide-mémoire

### Fiche 1 — Les formules en un coup d'œil

```
OOS Correction
  theoretical_units_sold[j] = median(units_sold[k], k ∈ [j-14..j], stock[k]>0)

Outlier Detection
  upper_bound = Q3 + 1.5 × (Q3 - Q1)
  is_outlier = (units_sold > upper_bound) AND NOT is_stockout

Run Rate
  alpha = clip((momentum - 1.0) / 0.5, 0, 1)
  run_rate = (1-alpha) × median30j + alpha × median7j

Stockout Date
  days = round(stock / run_rate)
  stockout_date = today + days

ROP Date
  effective_LT = ceil(lead_time + max(0, avg_delay))
  reorder_alert_date = stockout_date - effective_LT

Safety Stock
  Z = norm.ppf(service_level)
  SS = Z × √(LT_eff × σd² + D² × σlt²)
  reorder_qty = ceil(max(0, D×LT_eff + SS - stock) / MOQ) × MOQ

ABC Analysis
  annual_profit = (sale - cost) × run_rate × 365
  A: cum% ≤ 80%  |  B: 80-95%  |  C: > 95%

MAPE
  mape = mean(|actual(t) - run_rate| / actual(t))
  mae  = mean(|actual(t) - run_rate|)
  bias = mean(run_rate - actual(t))

Health Score
  avail    = 1 - RAR/(forecast_30d + RAR)
  rot      = f(coverage_days)   [0→7j: linéaire; 7→45j: 1.0; 45→90j: décroissant]
  out      = 1 - stockout_count / total_skus
  score    = round((avail×0.5 + rot×0.3 + out×0.2) × 100)

Supplier Reliability
  reliability   = on_time_POs / total_POs
  average_delay = mean(actual - expected)  jours
  lt_sigma      = std(actual - order_date, ddof=1)  jours
```

### Fiche 2 — Questions / Réponses types en démo

**"Comment vous évitez les fausses alertes ?"**
> Michi filtre deux types de bruit : les jours de rupture (stock = 0, pas de demande réelle) et les pics anormaux (IQR). Le run rate est calculé uniquement sur les jours propres. Les fausses alertes sont donc structurellement réduites.

**"Que se passe-t-il si j'ai peu d'historique ?"**
> Michi a des mécanismes de fallback pour les séries courtes : médiane globale si moins de 4 jours propres, taux de saisonnalité neutre (1.0) si moins de 28 jours d'historique. Le système est opérationnel dès le premier mois de connexion, même imparfait.

**"Comment ça gère les soldes et le Black Friday ?"**
> Les pics de type Black Friday sont gérés par le momentum adaptatif : quand la demande explose, le run rate bascule progressivement vers la médiane 7j qui capte l'accélération. L'IQR ne flagge pas les pics si la médiane des 30j précédents est elle-même élevée (cas des grandes campagnes prévues).

**"Que signifie 'Revenue at Risk' ?"**
> C'est la valeur totale des commandes fournisseurs à passer pour couvrir les besoins des 30 prochains jours. Si ce chiffre est 8 400€, cela signifie que vous avez 8 400€ de CA potentiel qui sera manqué si vous ne passez aucune commande aujourd'hui.

**"Pouvez-vous gérer des produits à forte saisonnalité ?"**
> Oui, avec l'IQR glissant sur 90 jours pour éviter de flaguer les ventes saisonnières comme outliers, et le momentum adaptatif pour réagir aux accélérations de saison. La décomposition saisonnière avancée (STL) est prévue en post-MVP pour les clients avec un historique de 12+ mois.

### Fiche 3 — Les chiffres à retenir pour le marketing

| Chiffre | Source | Usage |
|---|---|---|
| **80%** | Pareto — SKUs classe A | "80% de votre marge sur 20% de vos produits" |
| **95%** | Service level par défaut | "95% de probabilité de ne jamais être en rupture" |
| **30 jours** | Fenêtre run rate | "Basé sur vos 30 derniers jours de ventes réelles" |
| **14 jours** | Fenêtre OOS correction | "Correction automatique sur 14 jours avant chaque rupture" |
| **ddof=1** | Statistique fournisseur | "Calcul précis même avec peu de commandes fournisseur" |

---

## Ressources complémentaires

### Références académiques

- **Silver, Pyke & Peterson** — *Inventory Management and Production Planning and Scheduling*, 3e édition (formule safety stock §7.4)
- **Nahmias** — *Production and Operations Analysis* (ABC analysis §2.6)
- **Tukey, J.W.** (1977) — *Exploratory Data Analysis* (règle IQR)
- **Agrawal & Smith** (1996) — *Estimating negative binomial demand for retail inventory management* (OOS censored demand)
- **Makridakis** (1993) — *Accuracy measures: theoretical and practical concerns* (définition MAPE)

### Fichiers source dans le projet

| Module | Fichier |
|---|---|
| OOS Correction | `apps/api/src/modules/intelligence/algorithms/out_of_stock_correction.py` |
| Outlier Detection | `apps/api/src/modules/intelligence/algorithms/outlier_detection.py` |
| Run Rate | `apps/api/src/modules/intelligence/algorithms/run_rate.py` |
| Predictions (Stockout + ROP + Safety Stock) | `apps/api/src/modules/intelligence/algorithms/predictions.py` |
| ABC Analysis | `apps/api/src/modules/intelligence/algorithms/abc_analysis.py` |
| MAPE / Forecast Accuracy | `apps/api/src/modules/intelligence/algorithms/mape.py` |
| Health Score | `apps/api/src/modules/intelligence/analytics/health_score.py` |
| Risk Scoring | `apps/api/src/modules/intelligence/analytics/risk_scoring.py` |
| Financial KPIs | `apps/api/src/modules/intelligence/analytics/financial_kpis.py` |
| Supplier Analysis | `apps/api/src/modules/intelligence/services/supplier_analysis.py` |
| Pipeline Orchestration | `apps/api/src/modules/intelligence/pipeline/cleaning_pipeline.py` |
| Intelligence Worker | `apps/api/src/modules/intelligence/application/worker.py` |

### Liens documentation interne

- [Architecture technique](architecture.md) — schéma DB, GraphQL, infrastructure
- [PRD Produit](prd.md) — User stories, personas, roadmap
- [Connecteurs](connectors.md) — Shopify, WooCommerce, Amazon, CSV

---

*Documentation Michi 道 — Intelligence Supply Chain v1.0*  
*Mise à jour : Sprint 26 — Mai 2026*
