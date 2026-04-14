---
id: overview
title: Moteur d'Intelligence
sidebar_label: 🧠 Introduction
sidebar_position: 1
---

# Moteur d'Intelligence Michi 道

Le module `intelligence/` constitue le cœur analytique de Michi 道. Contrairement aux approches traditionnelles basées sur des moyennes simples, Michi utilise des estimateurs robustes pour traiter les bruits inévitables de l'e-commerce (ruptures, promotions, erreurs de saisie).

## 🛡️ Robustesse Statistique

### Médiane vs Moyenne
Dans un flux de ventes e-commerce, une seule "grosse vente" (B2B ou erreur) peut fausser une moyenne sur 30 jours, entraînant un surstockage inutile.

Michi privilégie la **Médiane** ($\tilde{x}$) comme indicateur de tendance centrale :
- **Moyenne ($\bar{x}$) :** Très sensible aux valeurs extrêmes.
- **Médiane ($\tilde{x}$) :** Représente la demande "typique" du consommateur.

## ⚙️ Architecture du Module
Le module est conçu comme un **Bounded Context** purement mathématique :
- **Zéro Dépendance :** Ne connaît ni la base de données, ni l'API.
- **Vectorisé :** Utilise Pandas et NumPy pour traiter des milliers de SKUs en quelques millisecondes.
- **Testable :** Chaque formule est validée par des tests unitaires avec des datasets limites (MAPE targeting).

---

:::info Pipeline de Données
L'intelligence s'applique en deux phases :
1. **Nettoyage :** Correction des ruptures et filtrage des anomalies.
2. **Prévision :** Calcul de la cadence de vente et projection de stock.
:::
