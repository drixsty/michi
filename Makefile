.PHONY: help install dev-backend dev-frontend dev-mobile api web mobile docs test test-all test-cov test-ui clean docker-up docker-down seed schema

help: ## Affiche l'aide
	@echo "Michi 道 - Commandes disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installe toutes les dépendances (backend + frontend)
	@echo "📦 Installation root..."
	npm install
	@echo "📦 Installation backend..."
	cd apps/api && pip install -r requirements.txt
	@echo ""
	@echo "📦 Installation frontend..."
	cd apps/web && npm install
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
	cd apps/api && python -m alembic upgrade head && python scripts/seed_dev_data.py

seed-v2: ## Seed la DB v2 (SaaS Multi-Tenant Enterprise) [S16]
	@echo "🌱 Seeding database v2 (SaaS)..."
	cd apps/api && set PYTHONPATH=. && python scripts/seed_v2.py

seed-demo: ## Régénère le dataset mock démo (50 produits + 365j historique)
	@echo "🌱 Seeding demo data..."
	cd apps/api && python scripts/seed_demo.py

seed-demo-small: ## Régénère un dataset mock réduit (10 produits — tests rapides)
	@echo "🌱 Seeding small demo data..."
	cd apps/api && python scripts/seed_demo.py --count 10

schema: ## Exporte le schéma GraphQL (SDL)
	@echo "📡 Exportation du schéma GraphQL..."
	cd apps/api && set PYTHONPATH=. && python scripts/export_schema.py > ../../packages/types/schema.graphql
	@echo "✅ Schéma exporté dans packages/types/schema.graphql"

api: dev-backend ## Alias pour dev-backend
web: dev-frontend ## Alias pour dev-frontend
mobile: dev-mobile ## Alias pour dev-mobile

dev-backend: ## Lance le backend (port 8000)
	@echo "🚀 Démarrage backend..."
	cd apps/api && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Lance le frontend (port 3000)
	@echo "🚀 Démarrage frontend..."
	cd apps/web && npm run dev

dev-mobile: ## Lance l'application mobile (Expo)
	@echo "🚀 Démarrage mobile..."
	cd apps/mobile && npx expo start

test: ## Lance tous les tests (backend + frontend + ui)
	@echo "🧪 Tests backend..."
	cd apps/api && pytest
	@echo ""
	@echo "🧪 Tests frontend..."
	cd apps/web && npm run test -- --run
	@echo ""
	@echo "🧪 Tests packages/ui..."
	cd packages/ui && npm run test

test-all: test ## Alias pour test (make test:all non supporté en Make)

test-ui: ## Lance les tests du Design System packages/ui
	@echo "🧪 Tests packages/ui..."
	cd packages/ui && npm run test

test-cov: ## Lance les tests backend avec coverage
	@echo "🧪 Tests avec coverage..."
	cd apps/api && pytest --cov=src --cov-report=html --cov-report=term

docs: ## Lance le serveur de documentation Docusaurus
	@echo "📚 Démarrage documentation..."
	cd docs-site && npm run start

clean: ## Nettoie les fichiers temporaires
	@echo "🧹 Nettoyage..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/api/htmlcov apps/api/.coverage
	@echo "✅ Nettoyage terminé !"

setup: docker-up install seed ## Setup complet du projet
	@echo ""
	@echo "✨ Projet Michi initialisé !"
	@echo ""
	@echo "🔗 Prochaines étapes:"
	@echo "  1. Démarrer le backend  : make api"
	@echo "  2. Démarrer le frontend : make web"
	@echo "  3. Ouvrir http://localhost:3000/login"
	@echo ""
	@echo "📧 Credentials:"
	@echo "  Email    : dev@michi.com"
	@echo "  Password : password123"
