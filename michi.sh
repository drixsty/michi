#!/usr/bin/env bash
set -e

COMMAND="${1:-help}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo -e "\033[0;36mMichi - Commandes disponibles:\033[0m"
    echo ""
    echo "  install        Installe toutes les dependances (root + api + web)"
    echo "  setup          Setup complet (docker-up + install + seed)"
    echo "  api            Lance le backend (port 8000)"
    echo "  web            Lance le frontend (port 3000)"
    echo "  docs           Lance le serveur de documentation (Docusaurus)"
    echo "  docker-up      Demarre PostgreSQL + Redis"
    echo "  docker-down    Arrete les services Docker"
    echo "  seed           Seed la DB (migrations + demo data)"
    echo "  schema         Exporte le schema GraphQL (SDL)"
    echo "  test           Lance tous les tests (api + web + ui)"
    echo "  test-cov       Lance les tests API avec coverage"
    echo "  clean          Nettoie les fichiers temporaires"
    echo "  help           Affiche cette aide"
    echo ""
}

case "$COMMAND" in
    install)
        echo -e "\033[0;33m[INFO] Installation root npm...\033[0m"
        npm install
        echo -e "\n\033[0;33m[INFO] Installation API (Python)...\033[0m"
        cd "$SCRIPT_DIR/apps/api" && pip install -r requirements.txt && cd "$SCRIPT_DIR"
        echo -e "\n\033[0;33m[INFO] Installation Web (npm)...\033[0m"
        cd "$SCRIPT_DIR/apps/web" && npm install && cd "$SCRIPT_DIR"
        echo -e "\n\033[0;32m[OK] Installation terminee !\033[0m"
        ;;

    docker-up)
        echo -e "\033[0;33m[DOCKER] Demarrage Docker services...\033[0m"
        docker-compose up -d
        echo -e "\033[0;33m[WAIT] Attente 5 secondes (demarrage DB)...\033[0m"
        sleep 5
        echo -e "\033[0;32m[OK] Services demarres !\033[0m"
        docker-compose ps
        ;;

    docker-down)
        echo -e "\033[0;33m[DOCKER] Arret Docker services...\033[0m"
        docker-compose down
        echo -e "\033[0;32m[OK] Services arretes !\033[0m"
        ;;

    seed)
        echo -e "\033[0;33m[SEED] Seeding database v2 (SaaS)...\033[0m"
        cd "$SCRIPT_DIR/apps/api" && PYTHONPATH=src python -m alembic upgrade head && PYTHONPATH=src python scripts/seed_v2.py && cd "$SCRIPT_DIR"
        ;;

    api)
        echo -e "\033[0;36m[RUN] Demarrage API (FastAPI)...\033[0m"
        cd "$SCRIPT_DIR/apps/api" && PYTHONPATH=src python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
        ;;

    web)
        echo -e "\033[0;36m[RUN] Demarrage Web App (Next.js)...\033[0m"
        cd "$SCRIPT_DIR/apps/web" && npm run dev
        ;;

    docs)
        echo -e "\033[0;36m[RUN] Demarrage Documentation (Docusaurus)...\033[0m"
        cd "$SCRIPT_DIR/docs-site" && npm run start
        ;;

    schema)
        echo -e "\033[0;33m[SDL] Exportation du schema GraphQL...\033[0m"
        export PYTHONPATH="."
        cd "$SCRIPT_DIR/apps/api" && python scripts/export_schema.py > "$SCRIPT_DIR/packages/types/schema.graphql" && cd "$SCRIPT_DIR"
        echo -e "\033[0;32m[OK] Schema exporte dans packages/types/schema.graphql\033[0m"
        ;;

    test)
        echo -e "\033[0;33m[TEST] Tests API (Pytest)...\033[0m"
        cd "$SCRIPT_DIR/apps/api" && pytest && cd "$SCRIPT_DIR"
        echo -e "\n\033[0;33m[TEST] Tests Web (Vitest)...\033[0m"
        cd "$SCRIPT_DIR/apps/web" && npm test -- --run && cd "$SCRIPT_DIR"
        echo -e "\n\033[0;33m[TEST] Tests UI Package...\033[0m"
        cd "$SCRIPT_DIR/packages/ui" && npm test && cd "$SCRIPT_DIR"
        ;;

    test-cov)
        echo -e "\033[0;33m[TEST] Tests API avec coverage...\033[0m"
        cd "$SCRIPT_DIR/apps/api" && pytest --cov=src --cov-report=html --cov-report=term && cd "$SCRIPT_DIR"
        ;;

    clean)
        echo -e "\033[0;33m[CLEAN] Nettoyage...\033[0m"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
        rm -rf apps/api/htmlcov apps/api/.coverage 2>/dev/null || true
        echo -e "\033[0;32m[OK] Nettoyage termine !\033[0m"
        ;;

    setup)
        bash "$0" docker-up
        bash "$0" install
        bash "$0" seed
        echo -e "\n\033[0;32m[DONE] Projet Michi initialise (Monorepo) !\033[0m"
        echo -e "\n[INFO] Prochaines etapes:"
        echo "  1. Demarrer le backend  : ./michi.sh api"
        echo "  2. Demarrer le frontend : ./michi.sh web"
        echo "  3. Consulter la doc     : ./michi.sh docs"
        ;;

    help|*)
        show_help
        ;;
esac
