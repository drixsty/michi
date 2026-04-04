# 🚀 Michi - Démarrage Ultra-Rapide (5 minutes)

## ⚡ Installation Express

### Prérequis Vérification
```bash
# Vérifier installations
python --version   # Doit être 3.11+
node --version     # Doit être 18+
docker --version   # Doit être 20.10+
```

### Étape 1 : Setup Automatique (Makefile)

```bash
cd michi-app

# Installation complète (services + dépendances + seed DB)
make setup
```

**Cette commande fait TOUT :**
- ✅ Démarre PostgreSQL + Redis (Docker)
- ✅ Installe dépendances backend (pip)
- ✅ Installe dépendances frontend (npm)
- ✅ Crée les tables DB
- ✅ Seed un user de développement

**Durée : ~3 minutes**

---

### Étape 2 : Lancer Backend (Terminal 1)

```bash
make dev-backend
```

**Backend ready sur :**
- 🚀 API : http://localhost:8000
- 📊 GraphQL : http://localhost:8000/graphql
- 📖 Docs : http://localhost:8000/docs

---

### Étape 3 : Lancer Frontend (Terminal 2)

```bash
make dev-frontend
```

**Frontend ready sur :**
- 💜 App : http://localhost:3000

---

### Étape 4 : Login

Ouvrir http://localhost:3000/login

**Credentials :**
```
Email    : dev@michi.com
Password : password123
```

---

## 📋 Commandes Utiles

```bash
make help           # Liste toutes les commandes
make test           # Lance les tests
make test-cov       # Tests avec coverage
make docker-up      # Démarre services Docker
make docker-down    # Arrête services Docker
make clean          # Nettoie les fichiers temporaires
```

---

## 🐛 Troubleshooting

### Port 8000 déjà utilisé
```bash
# Trouver le processus
lsof -i :8000
# Tuer le processus
kill -9 <PID>
```

### Port 3000 déjà utilisé
```bash
# Changer le port Next.js
cd frontend
PORT=3001 npm run dev
```

### Docker services ne démarrent pas
```bash
# Vérifier Docker
docker ps
docker-compose logs

# Redémarrer
make docker-down
make docker-up
```

### Erreur "Module not found"
```bash
# Réinstaller dépendances
make install
```

---

## 📁 Structure du Projet

```
michi-app/
├── backend/           ← Python FastAPI + GraphQL
├── frontend/          ← Next.js 14 + React
├── docker-compose.yml ← PostgreSQL + Redis
├── Makefile           ← Commandes utiles
└── README.md          ← Documentation complète
```

---

## 🎯 Prochaines Étapes

1. ✅ **Tester l'authentification** : Login/Logout sur l'app
2. ✅ **Explorer GraphQL Playground** : http://localhost:8000/graphql
3. 📚 **Lire la doc complète** : [README.md](../README.md)
4. 🧪 **Lancer les tests** : `make test`
5. 🛠️ **Commencer Epic 1** : Mock Shopify data generator

---

## 📚 Documentation Complète

- **[README.md](../README.md)** : Documentation complète du projet
- **[prd.md](prd.md)** : Product Requirements (40+ pages)
- **[architecture.md](architecture.md)** : Architecture technique (50+ pages)
- **[claude.md](claude.md)** : Instructions pour agent IA (60+ pages)

---

## 🆘 Support

**Problème ?**
1. Vérifier les logs : `docker-compose logs`
2. Vérifier la doc : [README.md](../README.md)
3. Ouvrir une issue : GitHub Issues

---

**Bon développement ! 道 💜**
