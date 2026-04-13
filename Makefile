.PHONY: help install dev-backend dev-frontend test clean docker-up docker-down seed

help: ## Affiche l'aide
	@echo "Michi 道 - Commandes disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installe toutes les dépendances (backend + frontend)
	@echo "📦 Installation backend..."
	cd backend && pip install -r requirements.txt
	@echo ""
	@echo "📦 Installation frontend..."
	cd frontend && npm install
	@echo ""
	@echo "✅ Installation terminée !"

docker-up: ## Démarre PostgreSQL + Redis
	@echo "🐳 Démarrage Docker services..."
	docker-compose up -d
	@echo "⏳ Attente 5 secondes (démarrage DB)..."
	sleep 5
	@echo "✅ Services démarrés !"
	@docker-compose ps

docker-down: ## Arrête les services Docker
	@echo "🛑 Arrêt Docker services..."
	docker-compose down
	@echo "✅ Services arrêtés !"

seed: ## Seed la DB (crée tables + user de dev)
	@echo "🌱 Seeding database..."
	cd backend && python -m alembic upgrade head && python scripts/seed_dev_data.py

seed-v2: ## Seed la DB v2 (SaaS Multi-Tenant Enterprise) [S16]
	@echo "🌱 Seeding database v2 (SaaS)..."
	cd backend && set PYTHONPATH=. && python scripts/seed_v2.py

seed-demo: ## Régénère le dataset mock démo (50 produits + 365j historique)
	@echo "🌱 Seeding demo data..."
	cd backend && python scripts/seed_demo.py

seed-demo-small: ## Régénère un dataset mock réduit (10 produits — tests rapides)
	@echo "🌱 Seeding small demo data..."
	cd backend && python scripts/seed_demo.py --count 10

dev-backend: ## Lance le backend (port 8000)
	@echo "🚀 Démarrage backend..."
	cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Lance le frontend (port 3000)
	@echo "🚀 Démarrage frontend..."
	cd frontend && npm run dev

test: ## Lance tous les tests (backend)
	@echo "🧪 Tests backend..."
	cd backend && pytest
	@echo ""
	@echo "🧪 Tests frontend..."
	cd frontend && npm test

test-cov: ## Lance les tests avec coverage
	@echo "🧪 Tests avec coverage..."
	cd backend && pytest --cov=src --cov-report=html --cov-report=term

clean: ## Nettoie les fichiers temporaires
	@echo "🧹 Nettoyage..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov backend/.coverage
	@echo "✅ Nettoyage terminé !"

setup: docker-up install seed ## Setup complet du projet
	@echo ""
	@echo "✨ Projet Michi initialisé !"
	@echo ""
	@echo "🔗 Prochaines étapes:"
	@echo "  1. Démarrer le backend  : make dev-backend"
	@echo "  2. Démarrer le frontend : make dev-frontend"
	@echo "  3. Ouvrir http://localhost:3000/login"
	@echo ""
	@echo "📧 Credentials:"
	@echo "  Email    : dev@michi.com"
	@echo "  Password : password123"
