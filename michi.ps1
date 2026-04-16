param (
    [Parameter(Mandatory=$false, Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Michi - Commandes disponibles (Windows PowerShell):" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  install        Installe toutes les dependances (root + api + web)"
    Write-Host "  setup          Setup complet (docker-up + install + seed)"
    Write-Host "  api            Lance le backend (port 8000)"
    Write-Host "  web            Lance le frontend (port 3000)"
    Write-Host "  docs           Lance le serveur de documentation (Docusaurus)"
    Write-Host "  docker-up      Demarre PostgreSQL + Redis"
    Write-Host "  docker-down    Arrete les services Docker"
    Write-Host "  seed           Seed la DB (migrations + demo data)"
    Write-Host "  schema         Exporte le schema GraphQL (SDL)"
    Write-Host "  test           Lance tous les tests (api + web + ui)"
    Write-Host "  clean          Nettoie les fichiers temporaires"
    Write-Host "  help           Affiche cette aide"
    Write-Host ""
}

switch ($Command) {
    "install" {
        Write-Host "[INFO] Installation des dependances (NPM Workspace)..." -ForegroundColor Yellow
        npm install
        Write-Host "`n[INFO] Installation API (Python)..." -ForegroundColor Yellow
        Set-Location apps/api; pip install -r requirements.txt; Set-Location ../..
        Write-Host "`n[OK] Installation terminee !" -ForegroundColor Green
    }

    "docker-up" {
        Write-Host "[DOCKER] Demarrage Docker services..." -ForegroundColor Yellow
        docker-compose up -d
        Write-Host "[WAIT] Attente 5 secondes (demarrage DB)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        Write-Host "[OK] Services demarres !" -ForegroundColor Green
        docker-compose ps
    }

    "docker-down" {
        Write-Host "[DOCKER] Arret Docker services..." -ForegroundColor Yellow
        docker-compose down
        Write-Host "[OK] Services arretes !" -ForegroundColor Green
    }

    "seed" {
        Write-Host "[SEED] Seeding database v2 (SaaS)..." -ForegroundColor Yellow
        $env:PYTHONPATH="src"
        Set-Location apps/api; python -m alembic upgrade head; python scripts/seed_v2.py; Set-Location ../..
    }

    "api" {
        Write-Host "[RUN] Demarrage API (FastAPI)..." -ForegroundColor Cyan
        $env:PYTHONPATH = "src"
        Set-Location apps/api; python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000; Set-Location ../..
    }

    "web" {
        Write-Host "[RUN] Demarrage Web App (Next.js)..." -ForegroundColor Cyan
        Set-Location apps/web; npm run dev; Set-Location ../..
    }

    "docs" {
        Write-Host "[RUN] Demarrage Documentation (Docusaurus)..." -ForegroundColor Cyan
        Set-Location docs-site; npm run start; Set-Location ..
    }

    "schema" {
        Write-Host "[SDL] Exportation du schema GraphQL..." -ForegroundColor Yellow
        $env:PYTHONPATH="."
        Set-Location apps/api; python scripts/export_schema.py | Out-File -FilePath "../../packages/types/schema.graphql" -Encoding utf8; Set-Location ../..
        Write-Host "[OK] Schéma exporté dans packages/types/schema.graphql" -ForegroundColor Green
    }

    "test" {
        Write-Host "[TEST] Tests API (Pytest)..." -ForegroundColor Yellow
        Set-Location apps/api; pytest; Set-Location ../..
        Write-Host "`n[TEST] Tests Web (Vitest)..." -ForegroundColor Yellow
        Set-Location apps/web; npm test -- --run; Set-Location ../..
        Write-Host "`n[TEST] Tests UI Package..." -ForegroundColor Yellow
        Set-Location packages/ui; npm test; Set-Location ../..
    }

    "test-cov" {
        Write-Host "[TEST] Tests API avec coverage..." -ForegroundColor Yellow
        Set-Location apps/api; pytest --cov=src --cov-report=html --cov-report=term; Set-Location ../..
    }

    "clean" {
        Write-Host "[CLEAN] Nettoyage..." -ForegroundColor Yellow
        Get-ChildItem -Path . -Filter "__pycache__" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Filter ".pytest_cache" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Filter "node_modules" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Filter ".next" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        if (Test-Path "apps/api/htmlcov") { Remove-Item -Path "apps/api/htmlcov" -Force -Recurse }
        if (Test-Path "apps/api/.coverage") { Remove-Item -Path "apps/api/.coverage" -Force }
        Write-Host "[OK] Nettoyage termine !" -ForegroundColor Green
    }

    "setup" {
        & $PSCommandPath "docker-up"
        & $PSCommandPath "install"
        & $PSCommandPath "seed"
        Write-Host "`n[DONE] Projet Michi initialise (Monorepo) !" -ForegroundColor Green
        Write-Host "`n[INFO] Prochaines etapes:"
        Write-Host "  1. Demarrer le backend  : .\michi.ps1 api"
        Write-Host "  2. Demarrer le frontend : .\michi.ps1 web"
        Write-Host "  3. Consulter la doc     : .\michi.ps1 docs"
    }

    Default {
        Show-Help
    }
}
