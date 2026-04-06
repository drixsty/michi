param (
    [Parameter(Mandatory=$false, Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Michi - Commandes disponibles (Windows PowerShell):" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  install        Installe toutes les dependances (backend + frontend)"
    Write-Host "  setup          Setup complet (docker-up + install + seed)"
    Write-Host "  dev-backend    Lance le backend (port 8000)"
    Write-Host "  dev-frontend   Lance le frontend (port 3000)"
    Write-Host "  docker-up      Demarre PostgreSQL + Redis"
    Write-Host "  docker-down    Arrete les services Docker"
    Write-Host "  seed           Seed la DB (cree tables + user de dev)"
    Write-Host "  test           Lance tous les tests (backend + frontend)"
    Write-Host "  clean          Nettoie les fichiers temporaires"
    Write-Host "  help           Affiche cette aide"
    Write-Host ""
}

switch ($Command) {
    "install" {
        Write-Host "[INFO] Installation backend..." -ForegroundColor Yellow
        Set-Location backend; pip install -r requirements.txt; Set-Location ..
        Write-Host "`n[INFO] Installation frontend..." -ForegroundColor Yellow
        Set-Location frontend; npm install; Set-Location ..
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
        Write-Host "[SEED] Seeding database..." -ForegroundColor Yellow
        Set-Location backend; python scripts/seed_dev_data.py; Set-Location ..
    }

    "dev-backend" {
        Write-Host "[RUN] Demarrage backend..." -ForegroundColor Cyan
        Set-Location backend; python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000; Set-Location ..
    }

    "dev-frontend" {
        Write-Host "[RUN] Demarrage frontend..." -ForegroundColor Cyan
        Set-Location frontend; npm run dev; Set-Location ..
    }

    "test" {
        Write-Host "[TEST] Tests backend..." -ForegroundColor Yellow
        Set-Location backend; pytest; Set-Location ..
        Write-Host "`n[TEST] Tests frontend..." -ForegroundColor Yellow
        Set-Location frontend; npm test; Set-Location ..
    }

    "test-cov" {
        Write-Host "[TEST] Tests avec coverage..." -ForegroundColor Yellow
        Set-Location backend; pytest --cov=src --cov-report=html --cov-report=term; Set-Location ..
    }

    "clean" {
        Write-Host "[CLEAN] Nettoyage..." -ForegroundColor Yellow
        Get-ChildItem -Path . -Filter "__pycache__" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Filter ".pytest_cache" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Filter "node_modules" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Filter ".next" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        if (Test-Path "backend/htmlcov") { Remove-Item -Path "backend/htmlcov" -Force -Recurse }
        if (Test-Path "backend/.coverage") { Remove-Item -Path "backend/.coverage" -Force }
        Write-Host "[OK] Nettoyage termine !" -ForegroundColor Green
    }

    "setup" {
        & $PSCommandPath "docker-up"
        & $PSCommandPath "install"
        & $PSCommandPath "seed"
        Write-Host "`n[DONE] Projet Michi initialise !" -ForegroundColor Green
        Write-Host "`n🔗 Prochaines etapes:"
        Write-Host "  1. Demarrer le backend  : .\michi.ps1 dev-backend"
        Write-Host "  2. Demarrer le frontend : .\michi.ps1 dev-frontend"
        Write-Host "  3. Ouvrir http://localhost:3000/login"
        Write-Host "`n📧 Credentials:"
        Write-Host "  Email    : dev@michi.com"
        Write-Host "  Password : password123"
    }

    Default {
        Show-Help
    }
}
