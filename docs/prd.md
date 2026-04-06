# Product Requirements Document (PRD) - Michi 道 OMNICANAL

**Version:** 5.0 (Sprint 6 Polish + Roadmap V2)  
**Date:** Avril 2026  
**Statut:** En développement - Phase Blindage MVP  
**Propriétaire Produit:** [Votre Nom]  
**Équipe:** Full-Stack + Data Science

---

## Table des Matières

1. [Vision & Objectifs](#1-vision--objectifs)
2. [Contexte Business](#2-contexte-business)
3. [User Personas](#3-user-personas)
4. [Epics & User Stories Détaillées](#4-epics--user-stories-détaillées)
5. [Wireframes & Flows](#5-wireframes--flows)
6. [Critères d'Acceptation](#6-critères-dacceptation)
7. [Priorités & Roadmap](#7-priorités--roadmap)
8. [Métriques de Succès](#8-métriques-de-succès)
9. [Contraintes & Dépendances](#9-contraintes--dépendances)
10. [Open Questions](#10-open-questions)

---

## 1. Vision & Objectifs

### 1.1 Vision Produit
**"Michi est le GPS des stocks e-commerce : anticiper, commander juste, ne jamais être en rupture."**

Michi transforme la gestion de stock d'une tâche complexe Excel en un tableau de bord simple et OMNICANAL qui dit :
- ⚠️ **"Tu vas être en rupture dans 12 jours"**
- 📦 **"Commande 150 unités maintenant (Source: Shopify + Amazon)"**
- 💰 **"Tu perds 2 400€/mois en ruptures"**

### 1.2 Objectifs du MVP
**Phase 0 (Current)** : Validation du problème
- ✅ 10 discovery interviews avec e-commerces mode
- ✅ 3 POC gratuits avec données réelles
- 🎯 Objectif : 1 utilisateur payant

**Phase MVP (3 mois)** :
- 🎯 **Objectif #1 :** Réduire les ruptures de stock de 40% pour 5 clients pilotes
- 🎯 **Objectif #2 :** Prouver la valeur avec €10K+ de manque à gagner évité par client
- 🎯 **Objectif #3 :** Obtenir 2 case studies documentés

### 1.3 Non-Objectifs (Out of Scope MVP)
❌ Multi-shop/multi-utilisateurs  
❌ Intégration directe Shopify API (Mock d'abord)  
❌ Prévisions multi-SKU complexes (ex: bundles)  
❌ Optimisation des commandes fournisseur multi-produits  
❌ Mobile app native (Responsive web suffit)

---

## 2. Contexte Business

### 2.1 Le Problème
**Pour qui :** E-commerces mode/beauté (50K-500K€ CA/an, 50-500 SKU, 1-5 personnes)

**Pain Points** (validés en interviews) :
1. **Ruptures coûteuses** : 4-8% du CA perdu en moyenne ([source: IHL Group](https://www.ihlservices.com/))
   - Exemple : Boutique à 300K€/an perd 12-24K€
2. **Surstocks immobilisent le cash** : 20-30% du capital bloqué
3. **Excel est chronophage** : 3-6h/semaine de gestion manuelle
4. **Pas d'expertise data** : Pas de data analyst in-house

**Alternatives actuelles :**
- **Excel/Sheets** (90% des TPE/PME) : Chronophage, erreurs humaines
- **Inventory Planner** ($500/mois) : Trop cher pour TPE
- **NetSuite/SAP** : Complexe, nécessite consultant

### 2.2 La Solution Michi
**Proposition de valeur unique :**
> "Arrêtez de deviner. Commandez juste. En 3 clics."

**Différenciation :**
- ✅ **No-code** : Zéro configuration technique
- ✅ **Prix accessible** : €49-149/mois (vs €500+ concurrents)
- ✅ **Onboarding < 10 minutes** : Upload CSV → Insights immédiats
- ✅ **IA prête à l'emploi** : Algorithmes pré-entraînés, pas de tuning

---

## 3. User Personas

### Persona #1 : Sophie, Fondatrice E-commerce Mode
**Profil :**
- Femme, 32 ans, fondatrice "La Garde-Robe Parisienne"
- CA : 180K€/an, 150 SKU (robes, chemisiers, pantalons)
- Équipe : Elle + 1 assistant logistique à temps partiel
- Outils : Shopify, Excel, Instagram

**Jobs-to-be-Done :**
- 🎯 "Je veux savoir **quand** commander **combien** d'unités pour chaque produit"
- 🎯 "Je veux éviter les ruptures sur mes best-sellers sans bloquer trop de cash"
- 🎯 "Je veux passer moins de temps sur Excel (actuellement 4h/semaine)"

**Frustrations :**
- 😤 "Mon best-seller (robe été) était en rupture pendant 3 semaines → -8K€"
- 😤 "J'ai commandé 200 pantalons... j'en ai vendu 30 en 6 mois"
- 😤 "Je ne sais jamais si mes prévisions Excel sont bonnes"

**Critères de succès :**
- Réduit les ruptures de 50%+
- Économise 3h+/semaine
- ROI clair en €

### Persona #2 : Marc, Data Scientist (Utilisateur Interne)
**Profil :**
- Homme, 28 ans, Data Scientist chez Michi
- Background : Python, ML, statistiques
- Responsabilité : Algorithmes de nettoyage et prédictions

**Jobs-to-be-Done :**
- 🎯 "Je veux tester mes algos sur des données réalistes (avec ruptures, outliers)"
- 🎯 "Je veux valider que le nettoyage Out-of-Stock corrige bien les biais"
- 🎯 "Je veux monitorer la qualité des prédictions en production"

**Critères de succès :**
- MAPE (Mean Absolute Percentage Error) < 15% sur 80% des SKU
- Zéro faux négatifs critiques (ruptures non détectées)

---

## 4. Epics & User Stories Détaillées

### Epic 0 : Authentification & Sécurité
**Priorité :** P0 (Bloquant)  
**Effort estimé :** 3 jours

#### US 0.1 : Login JWT
**En tant que** utilisateur (Sophie)  
**Je veux** me connecter avec email/mot de passe  
**Afin de** accéder à mon espace sécurisé et voir MES données uniquement

**Critères d'acceptation :**
- [ ] Formulaire login avec email + password
- [ ] Token JWT généré côté backend (expiration 24h)
- [ ] Token stocké dans localStorage (ou httpOnly cookie pour prod)
- [ ] Redirection automatique vers `/dashboard` après login réussi
- [ ] Message d'erreur clair si credentials incorrects
- [ ] Pas de données sensibles (password) dans localStorage

**Détails techniques :**
```graphql
mutation Login($email: String!, $password: String!) {
  login(email: $email, password: $password) {
    token
    user {
      id
      email
      shopId
    }
  }
}
```

**Cas limites :**
- Email non existant → "Identifiants incorrects"
- Password incorrect → "Identifiants incorrects" (même message pour sécurité)
- Token expiré → Déconnexion auto + redirect vers login

**Design Notes :**
- Écran centré, minimaliste, logo Michi (道)
- Bouton CTA purple #6C5CE7
- Lien "Mot de passe oublié ?" (hors MVP, affiche message "Contactez support")

---

#### US 0.2 : Protection API GraphQL
**En tant que** système backend  
**Je veux** bloquer toutes les requêtes GraphQL sans token JWT valide  
**Afin de** protéger les données sensibles de chaque shop

**Critères d'acceptation :**
- [ ] Middleware JWT vérifie le token sur TOUTES les queries/mutations (sauf `login`)
- [ ] Token invalide → Erreur `UNAUTHENTICATED` avec code 401
- [ ] Token expiré → Erreur `TOKEN_EXPIRED` avec code 401
- [ ] `shopId` extrait du token et injecté dans le context GraphQL
- [ ] Tests unitaires : requête sans token, token expiré, token manipulé

**Détails techniques :**
```python
# backend/src/core/middleware/auth.py
async def auth_middleware(info, **kwargs):
    token = extract_token_from_header(info.context.request)
    if not token:
        raise GraphQLError("Authentication required", extensions={"code": "UNAUTHENTICATED"})
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        info.context.user_id = payload["user_id"]
        info.context.shop_id = payload["shop_id"]
    except jwt.ExpiredSignatureError:
        raise GraphQLError("Token expired", extensions={"code": "TOKEN_EXPIRED"})
```

---

### Epic 1 : Ingestion des Données & Mock Shopify
**Priorité :** P0 (Bloquant)  
**Effort estimé :** 5 jours

#### US 1.1 : Générateur de Fausses Données (Seeding)
**En tant que** Data Scientist (Marc)  
**Je veux** un script de seeding qui génère des produits et un historique de ventes réaliste sur 365 jours  
**Afin de** tester les algorithmes de nettoyage et de prédiction sur des cas complexes

**Critères d'acceptation :**
- [ ] Script génère 50 produits avec SKU, titre, stock initial
- [ ] Historique de 365 jours de ventes par produit
- [ ] **Simulation de ruptures** : 10-15% des produits ont des périodes avec stock=0 pendant 3-21 jours
- [ ] **Simulation d'outliers** : 5% des jours ont des pics de ventes (Black Friday, soldes)
- [ ] **Saisons** : Produits "mode été" vendent plus Mai-Août
- [ ] Les données sont reproductibles (seed aléatoire fixe)

**Détails techniques :**
```python
# backend/src/modules/shopify/seed_mock_data.py
def generate_mock_sales(product_id: str, days: int = 365):
    """
    Génère un historique de ventes réaliste avec :
    - Tendance saisonnière (sin/cos)
    - Ruptures aléatoires (stock=0 pendant N jours)
    - Outliers (Black Friday, soldes)
    """
    base_run_rate = random.uniform(2, 10)  # Ventes/jour moyennes
    
    for day in range(days):
        # Saisonnalité
        seasonal_factor = 1 + 0.3 * math.sin(2 * math.pi * day / 365)
        
        # Rupture de stock (10% de chance)
        if random.random() < 0.1 and stock == 0:
            units_sold = 0  # Rupture
        else:
            units_sold = int(base_run_rate * seasonal_factor + random.gauss(0, 1))
        
        # Outliers (1% de chance)
        if random.random() < 0.01:
            units_sold *= random.uniform(3, 8)  # Pic de ventes
        
        daily_sales_logs.append({
            "product_id": product_id,
            "date": date.today() - timedelta(days=365-day),
            "units_sold": max(0, units_sold),
            "end_of_day_stock": stock
        })
```

**Cas de test :**
- Produit avec **0 ruptures** : Algorithme doit calculer run rate normal
- Produit avec **3 ruptures de 7 jours** : Algorithme doit interpoler les ventes perdues
- Produit avec **outlier Black Friday** : Algorithme doit lisser le pic

**Design Notes :**
- Commande CLI : `python seed_mock_data.py --days 365 --products 50`
- Log dans console : "✓ Généré 50 produits, 18 250 daily_sales_logs"

---

#### US 1.2 : Interface de Synchronisation (Bouton "Sync")
**En tant que** utilisateur (Sophie)  
**Je veux** cliquer sur un bouton "Synchroniser mes données"  
**Afin de** charger mes produits et historique de ventes dans Michi

**Critères d'acceptation :**
- [ ] Bouton "Synchroniser" visible sur `/dashboard` (header ou zone vide si aucun produit)
- [ ] Clic déclenche la mutation GraphQL `triggerMockDataSync`
- [ ] Spinner de chargement pendant la génération (5-10 secondes)
- [ ] Message de succès : "✓ 50 produits synchronisés, 365 jours d'historique"
- [ ] Redirection automatique vers `/dashboard` avec données visibles
- [ ] Gestion d'erreur : Si échec, message "⚠️ Erreur de synchronisation. Réessayez."

**Détails techniques :**
```graphql
mutation TriggerSync($days: Int!) {
  triggerMockDataSync(daysToGenerate: $days)
}
```

**Frontend (Next.js + Apollo) :**
```typescript
const [sync, { loading, error }] = useMutation(TRIGGER_SYNC);

const handleSync = async () => {
  try {
    await sync({ variables: { days: 365 } });
    toast.success("✓ Données synchronisées !");
    router.push("/dashboard");
  } catch (err) {
    toast.error("⚠️ Erreur de synchronisation");
  }
};
```

**Wireframe Textuel :**
```
┌─────────────────────────────────────┐
│  🏠 Dashboard                  [⚙️]  │
├─────────────────────────────────────┤
│                                     │
│      📦 Aucun produit détecté       │
│                                     │
│   Synchronisez vos données pour     │
│   commencer à prédire vos stocks    │
│                                     │
│   [🔄 Synchroniser maintenant]     │
│                                     │
└─────────────────────────────────────┘
```

---

### Epic 2 : Algorithmes de Nettoyage (Data Science)
**Priorité :** P0 (Bloquant)  
**Effort estimé :** 8 jours

#### US 2.1 : Correction des Ruptures (Out-of-Stock Correction)
**En tant que** algorithme de prédiction  
**Je veux** identifier les jours où `stock = 0` et corriger les ventes à 0 avec une estimation théorique  
**Afin de** calculer un Run Rate non-biaisé pour les prédictions

**Problème :**
```
Produit X - Historique brut :
Jour 1-10 : 5 ventes/jour (stock > 0)
Jour 11-15 : 0 ventes/jour (stock = 0 → RUPTURE)
Jour 16-20 : 5 ventes/jour (stock > 0)

❌ Run Rate brut = (5*10 + 0*5 + 5*5) / 20 = 3.75 ventes/jour
✅ Run Rate corrigé = (5*10 + [5]*5 + 5*5) / 20 = 5 ventes/jour
```

**Critères d'acceptation :**
- [ ] L'algorithme détecte tous les jours où `end_of_day_stock = 0`
- [ ] Pour chaque jour en rupture, calcule une "vente théorique" = moyenne mobile 14 jours avant
- [ ] Si rupture > 14 jours consécutifs, utilise moyenne pré-rupture uniquement
- [ ] Sauvegarde dans `cleaned_demand` : `theoretical_units_sold`, `is_outlier = False`
- [ ] Tests unitaires : Produit sans rupture, produit avec 1 rupture courte (3j), produit avec rupture longue (21j)

**Détails techniques :**
```python
# backend/src/modules/forecasting/algorithms/out_of_stock_correction.py
def correct_out_of_stock(df: pd.DataFrame) -> pd.DataFrame:
    """
    df contient : product_id, date, units_sold, end_of_day_stock
    Retourne df avec colonne 'theoretical_units_sold'
    """
    df = df.sort_values(['product_id', 'date'])
    
    for product_id in df['product_id'].unique():
        product_df = df[df['product_id'] == product_id].copy()
        
        # Détecter ruptures
        stockout_mask = product_df['end_of_day_stock'] == 0
        
        for idx in product_df[stockout_mask].index:
            # Moyenne mobile 14 jours avant
            window = product_df.loc[:idx-1].tail(14)
            avg_sales = window['units_sold'].mean()
            
            product_df.loc[idx, 'theoretical_units_sold'] = avg_sales
        
        # Remplir les non-ruptures
        product_df['theoretical_units_sold'].fillna(product_df['units_sold'], inplace=True)
        
        df.update(product_df)
    
    return df
```

**Validation (Data Science) :**
- MAPE sur produits SANS rupture : < 5% (validation que l'algo ne dégrade pas)
- MAPE sur produits AVEC ruptures : Run Rate corrigé doit être +30-50% vs brut

---

#### US 2.2 : Filtrage des Outliers (IQR Method)
**En tant que** algorithme de prédiction  
**Je veux** détecter et lisser les pics de ventes anormaux (Black Friday, erreurs de saisie)  
**Afin de** ne pas surestimer les commandes futures

**Critères d'acceptation :**
- [ ] L'algorithme calcule Q1, Q3 et IQR (Interquartile Range) pour chaque produit
- [ ] Seuil outlier : `valeur > Q3 + 1.5 * IQR`
- [ ] Les outliers sont remplacés par la médiane des 30 jours autour
- [ ] Sauvegarde dans `cleaned_demand` : `is_outlier = True` pour traçabilité
- [ ] Tests : Produit avec Black Friday (ventes x5), produit avec erreur de saisie (ventes x100)

**Détails techniques :**
```python
def detect_and_smooth_outliers(df: pd.DataFrame) -> pd.DataFrame:
    for product_id in df['product_id'].unique():
        product_df = df[df['product_id'] == product_id].copy()
        
        Q1 = product_df['theoretical_units_sold'].quantile(0.25)
        Q3 = product_df['theoretical_units_sold'].quantile(0.75)
        IQR = Q3 - Q1
        
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_mask = product_df['theoretical_units_sold'] > upper_bound
        
        for idx in product_df[outlier_mask].index:
            # Remplacer par médiane fenêtre 30j
            window = product_df.loc[idx-15:idx+15]
            median_sales = window['theoretical_units_sold'].median()
            
            product_df.loc[idx, 'theoretical_units_sold'] = median_sales
            product_df.loc[idx, 'is_outlier'] = True
        
        df.update(product_df)
    
    return df
```

---

### Epic 3 : Paramétrage & Prédictions
**Priorité :** P0 (Bloquant)  
**Effort estimé :** 6 jours

#### US 3.1 : Variables de Stock (Lead Time & MOQ)
**En tant que** utilisateur (Sophie)  
**Je veux** modifier le délai fournisseur (Lead Time) et la quantité minimale de commande (MOQ) pour chaque produit  
**Afin que** les prédictions tiennent compte de MES contraintes réelles

**Critères d'acceptation :**
- [ ] Colonne "Lead Time" et "MOQ" visibles dans le tableau produits
- [ ] Clic sur cellule → Champ éditable inline (ou modal)
- [ ] Validation : Lead Time entre 1-90 jours, MOQ > 0
- [ ] Sauvegarde automatique après modification (mutation GraphQL)
- [ ] Message de confirmation : "✓ Lead Time mis à jour"
- [ ] Calcul date de rupture se met à jour immédiatement

**Détails techniques :**
```graphql
mutation UpdateInventoryRules($productId: ID!, $leadTime: Int, $moq: Int) {
  updateProductInventoryRules(productId: $productId, leadTime: $leadTime, moq: $moq) {
    id
    leadTime
    moq
  }
}
```

**Wireframe Textuel :**
```
┌──────────────────────────────────────────────────────────┐
│  Produits                                                │
├──────────────────────────────────────────────────────────┤
│ SKU     │ Nom       │ Stock │ Lead Time │ MOQ │ Statut │
├─────────┼───────────┼───────┼───────────┼─────┼────────┤
│ RB-001  │ Robe Été  │ 12    │ [15j ▼]   │ 50  │ 🟢     │
│ PL-002  │ Pantalon  │ 3     │ [7j ▼]    │ 20  │ 🔴     │
└──────────────────────────────────────────────────────────┘
         Clic → Dropdown ou Input inline
```

---

#### US 3.2 : Calcul Date de Rupture
**En tant que** utilisateur (Sophie)  
**Je veux** voir une estimation de la date à laquelle chaque produit sera en rupture  
**Afin de** savoir QUAND je dois commander

**Formule :**
```
Date de Rupture = Date Actuelle + (Stock Actuel / Run Rate Nettoyé)

Exemple :
- Produit : Robe Été
- Stock actuel : 30 unités
- Run Rate nettoyé : 2.5 ventes/jour
- Calcul : 30 / 2.5 = 12 jours
- Date de rupture : Aujourd'hui + 12j = 16 Mars 2026
```

**Critères d'acceptation :**
- [ ] Colonne "Date de Rupture Prévue" visible dans tableau
- [ ] Calcul automatique pour tous les produits
- [ ] Si Run Rate = 0 (produit jamais vendu), afficher "Pas de prévision"
- [ ] Tri par défaut : Date de rupture la plus proche en haut
- [ ] Badge de priorité : 🔴 < 7 jours, 🟡 7-30 jours, 🟢 > 30 jours

**Détails techniques :**
```python
# backend/src/modules/forecasting/algorithms/predict_stockout.py
def calculate_stockout_date(product: Product, cleaned_demand: List[CleanedDemand]) -> date:
    """
    Calcule la date de rupture prévue
    """
    # Run Rate = Moyenne des 30 derniers jours de ventes nettoyées
    last_30_days = cleaned_demand[-30:]
    run_rate = sum([d.theoretical_units_sold for d in last_30_days]) / 30
    
    if run_rate == 0:
        return None  # Pas de prévision possible
    
    days_until_stockout = product.current_inventory / run_rate
    
    stockout_date = date.today() + timedelta(days=int(days_until_stockout))
    
    return stockout_date
```

---

#### US 3.3 : Recommandation d'Achat
**En tant que** utilisateur (Sophie)  
**Je veux** voir une quantité recommandée à commander pour chaque produit  
**Afin de** savoir COMBIEN commander pour éviter la rupture

**Formule :**
```
Quantité Recommandée = (Run Rate × (Lead Time + Stock de Sécurité)) - Stock Actuel

Arrondi au multiple supérieur de MOQ

Exemple :
- Run Rate : 2.5 unités/jour
- Lead Time : 15 jours
- Stock de Sécurité : 14 jours (paramètre système, 2 semaines par défaut)
- Stock actuel : 12 unités
- MOQ : 50

Calcul :
1. Besoin = 2.5 × (15 + 14) = 72.5 unités
2. À commander = 72.5 - 12 = 60.5 unités
3. Arrondi MOQ : ceil(60.5 / 50) × 50 = 100 unités
```

**Critères d'acceptation :**
- [ ] Colonne "Qté à Commander" visible
- [ ] Calcul respecte le Lead Time et la MOQ du produit
- [ ] Si Stock Actuel > Besoin, afficher "Stock suffisant" (pas de commande)
- [ ] Tooltip explique le calcul (hover sur icône ℹ️)
- [ ] Possibilité d'exporter la liste en CSV pour copier-coller vers le fournisseur

**Détails techniques :**
```python
def calculate_order_quantity(
    product: Product,
    run_rate: float,
    safety_stock_days: int = 14
) -> int:
    """
    Calcule la quantité recommandée à commander
    """
    # Besoin total = Run Rate × (Lead Time + Stock de Sécurité)
    total_need = run_rate * (product.lead_time_days + safety_stock_days)
    
    # Quantité à commander
    order_qty = total_need - product.current_inventory
    
    if order_qty <= 0:
        return 0  # Stock suffisant
    
    # Arrondir au multiple supérieur de MOQ
    moq_multiple = math.ceil(order_qty / product.moq)
    
    return moq_multiple * product.moq
```

---

### Epic 4 : UI/UX Dashboard
**Priorité :** P0 (Bloquant)  
**Effort estimé :** 7 jours

#### US 4.1 : Tableau de Bord (Liste Triée par Urgence)
**En tant que** utilisateur (Sophie)  
**Je veux** voir une liste claire de mes produits triée par urgence de commande  
**Afin de** savoir immédiatement quoi commander en priorité

**Critères d'acceptation :**
- [ ] Page `/dashboard` affiche tableau avec colonnes : SKU, Nom, Stock, Date Rupture, Qté à Commander, Statut
- [ ] Tri par défaut : Date de rupture la plus proche → la plus éloignée
- [ ] Badges de priorité :
  - 🔴 "Urgent" : < 7 jours
  - 🟡 "À surveiller" : 7-30 jours
  - 🟢 "Stock sain" : > 30 jours
- [ ] Recherche par SKU ou nom de produit
- [ ] Filtres : "Urgent uniquement", "Tous", "Stock sain"
- [ ] Pagination ou scroll infini si > 50 produits
- [ ] Responsive mobile : Tableau devient cartes empilées

**Design Inspirations :**
- **Linear** : Tableau épuré, badges colorés, tri intuitif
- **Stripe Dashboard** : KPI cards en haut, tableau en dessous
- **Notion** : Filtres et vues multiples

**Wireframe Desktop :**
```
┌─────────────────────────────────────────────────────────────────┐
│  道 Michi              [🔍 Rechercher...]  [Sophie ▼] [⚙️]      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 Dashboard                                                   │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                        │
│  │ 💰 12K€ │  │ ⚠️ 8    │  │ 📦 42   │                        │
│  │ Manque  │  │ Produits│  │ Produits│                        │
│  │ à gagner│  │ urgents │  │ totaux  │                        │
│  └─────────┘  └─────────┘  └─────────┘                        │
│                                                                 │
│  [🔴 Urgent] [🟡 À surveiller] [🟢 Tous]                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ SKU    │ Produit      │ Stock │ Rupture   │ Qté │ Statut│  │
│  ├────────┼──────────────┼───────┼───────────┼─────┼───────┤  │
│  │ RB-001 │ Robe Été     │ 3     │ 🔴 4 Mars │ 100 │ 🔴    │  │
│  │ PL-002 │ Pantalon     │ 12    │ 🟡 15 Mars│ 50  │ 🟡    │  │
│  │ CH-003 │ Chemise      │ 45    │ 🟢 2 Avril│ -   │ 🟢    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [📥 Exporter CSV]                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Wireframe Mobile :**
```
┌───────────────────────┐
│ 道 Michi        [☰]   │
├───────────────────────┤
│ 📊 Dashboard          │
│                       │
│ ┌───────────────────┐ │
│ │ 💰 Manque à gagner│ │
│ │ 12 400€           │ │
│ └───────────────────┘ │
│                       │
│ ┌───────────────────┐ │
│ │ 🔴 Robe Été       │ │
│ │ Stock: 3 unités   │ │
│ │ Rupture: 4 Mars   │ │
│ │ Commander: 100    │ │
│ └───────────────────┘ │
│                       │
│ ┌───────────────────┐ │
│ │ 🟡 Pantalon       │ │
│ │ Stock: 12 unités  │ │
│ │ Rupture: 15 Mars  │ │
│ │ Commander: 50     │ │
│ └───────────────────┘ │
└───────────────────────┘
```

---

#### US 4.2 : Design Mobile-First
**En tant que** utilisateur (Sophie)  
**Je veux** consulter mon dashboard sur smartphone  
**Afin de** vérifier mes stocks en déplacement (ex: chez fournisseur)

**Critères d'acceptation :**
- [ ] Toutes les pages fonctionnent sur écran 375px (iPhone SE)
- [ ] Tableau desktop → Cartes empilées sur mobile
- [ ] Boutons suffisamment grands (min 44x44px touch target)
- [ ] Pas de scroll horizontal (sauf tableaux optionnels)
- [ ] Testée sur Chrome Android, Safari iOS
- [ ] Performance : Lighthouse Mobile > 90

**Tech Stack Mobile :**
- Next.js (SSR pour SEO)
- Tailwind CSS (responsive utilities)
- shadcn/ui (composants accessibles)

---

## 5. Wireframes & Flows

### 5.1 User Flow Principal
```
[Login] → [Dashboard vide] → [Clic Sync] → [Chargement 5s] 
  ↓
[Dashboard avec données]
  ↓
[Voir produit en 🔴] → [Modifier Lead Time/MOQ] → [Voir nouvelle recommandation]
  ↓
[Exporter CSV] → [Commander chez fournisseur] → [Attendre livraison]
  ↓
[Retour Dashboard 2 semaines + tard] → [Badge passe 🔴 → 🟢]
```

### 5.2 Wireframe Complet - Dashboard
Voir section 4.1 ci-dessus.

---

## 6. Critères d'Acceptation

### 6.1 Critères Fonctionnels (Feature Complete)
- [ ] Toutes les US des Epic 0-4 sont implémentées et testées
- [ ] Aucun bug bloquant en QA
- [ ] Performance : Page load < 2s, interactions < 100ms

### 6.2 Critères Business (Product-Market Fit)
- [ ] 5 clients pilotes utilisent Michi en production
- [ ] Réduction moyenne des ruptures : > 35%
- [ ] Économies documentées : > €8K par client
- [ ] NPS (Net Promoter Score) : > 40

### 6.3 Critères Techniques (Production Ready)
- [ ] Tests unitaires : Couverture > 80%
- [ ] Tests e2e : 10 scénarios critiques automatisés (Playwright)
- [ ] Documentation API GraphQL complète (introspection + exemples)
- [ ] Monitoring : Sentry (errors), Vercel Analytics (frontend)

---

## 7. Priorités & Roadmap

### Phase 0 : Validation Problème (Terminé)
✅ 10 interviews  
✅ 3 POC gratuits  
🎯 1er client payant

### Epic 5 : Alerting & Safety Stock (Sprint 7)
**Priorité :** P0 (Hardening)  

#### US 5.1 : Système d'Alertes "Anti-Rupture"
**Fonctionnalité :** Notification proactive quand `Stock < (Sales * LeadTime) + SafetyBuffer`.

### Epic 6 : Gestion Fournisseurs (Sprint 8)
**Priorité :** P1 (Robustesse)

#### US 6.1 : Fiabilité Lead Times
**Fonctionnalité :** Calcul de l'écart entre délai annoncé et réel.

### Epic 7 : Connecteurs Omnicanaux (Sprint 9)
**Priorité :** P1 (Expansion)

#### US 7.1 : Ingestion Universelle
**Fonctionnalité :** Connecteurs pour Shopify, WooCommerce, Amazon et Import CSV.

### Epic 8 : Simulations & Trust (Sprint 10)
**Priorité :** P2 (Scale)

#### US 8.1 : Simulateur de Promotions
**Fonctionnalité :** "What-if" scenario pour les pics de demande futurs.

---

## 7. Priorités & Roadmap

### Phase 0 : Validation Problème (Terminé)
✅ 10 interviews  
✅ 3 POC gratuits  
🎯 1er client payant

### Phase MVP (Sprints 1-6 - Terminé/Polish)
✅ Sprint 1-5 : Infrastructure, Algos, Prédictions  
🚀 Sprint 6 : Dashboard Premium & Polish Final

### Phase Blindage Omnicanal (Nouveau - Q3 2026)
**Sprint 7 :** Alerting Proactif & Safety Stock  
**Sprint 8 :** Gestion Fournisseurs & Lead Times  
**Sprint 9 :** Connecteurs Omnicanaux (Aggregator)  
**Sprint 10 :** Simulateur de Croissance & Trust Widgets

---

## 8. Métriques de Succès

### 8.1 Métriques Produit (Leading Indicators)
- **Adoption :** 5 clients pilotes actifs dans les 3 mois MVP
- **Engagement :** 80%+ se connectent 2x/semaine minimum
- **Rétention :** 90%+ des pilotes continuent après 3 mois

### 8.2 Métriques Business (Lagging Indicators)
- **Réduction ruptures :** Moyenne -40% (objectif -35%)
- **Économies client :** Médiane €10K+ par an
- **ROI :** Payback < 2 mois pour client moyen

### 8.3 Métriques Techniques
- **Précision prédictions :** MAPE < 15% sur 80% des SKU
- **Uptime :** > 99.5%
- **Latence API :** p95 < 200ms

---

## 9. Contraintes & Dépendances

### 9.1 Contraintes Techniques
- Pas d'accès Shopify API pour MVP → Mock obligatoire
- Backend Python (Data Science) → Stack moins commune que Node
- Déploiement Vercel (frontend) + Railway/Render (backend)

### 9.2 Dépendances
- **Bloquant :** Accès à des données réelles pour valider algos (résolu via clients pilotes)
- **Critique :** Design system (shadcn/ui) doit être stable
- **Nice-to-have :** Stripe intégration (post-MVP)

---

## 10. Open Questions

### 10.1 Questions Produit
❓ **Stock de sécurité :** 14 jours par défaut, ou personnalisable par utilisateur ?  
→ Décision : 14j fixe pour MVP, paramétrable post-MVP

❓ **Alertes email :** Automatiques ou opt-in uniquement ?  
→ Décision : Post-MVP, opt-in

### 10.2 Questions Techniques
❓ **GraphQL subscriptions** pour live updates du dashboard ?  
→ Décision : Polling 60s suffit pour MVP, subscriptions post-MVP

❓ **Déploiement backend** : Railway, Render ou AWS Lambda ?  
→ Décision : Railway pour MVP (simplicité), AWS si scale post-MVP

---

## Annexes

### A. Glossaire
- **Run Rate :** Vitesse de vente moyenne (unités/jour)
- **Lead Time :** Délai entre commande et réception (jours)
- **MOQ :** Minimum Order Quantity (quantité minimale de commande)
- **Out-of-Stock :** Rupture de stock (inventaire = 0)
- **MAPE :** Mean Absolute Percentage Error (métrique de précision)

### B. Références
- [IHL Group - Cost of Stockouts](https://www.ihlservices.com/)
- [Shopify API Docs](https://shopify.dev/docs/api)
- [Linear Product Principles](https://linear.app/method)
- [Stripe Dashboard Design](https://stripe.com/docs/dashboard)

---

**Fin du PRD v2.0**
