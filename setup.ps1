# Kaushal Prativedan Portal - First-time Setup Script
# Run this after git clone / git pull on a new machine.

$ErrorActionPreference = "Stop"

Write-Host "=== Kaushal Prativedan Portal Setup ===" -ForegroundColor Cyan

# --- Backend .env ---
$backendEnv = "backend\.env"
$backendExample = "backend\.env.example"

if (-not (Test-Path $backendEnv)) {
    if (Test-Path $backendExample) {
        Copy-Item $backendExample $backendEnv
        Write-Host "[OK] Created $backendEnv from $backendExample" -ForegroundColor Green
        Write-Host "     >> Edit $backendEnv and set DATABASE_URL to your PostgreSQL connection string." -ForegroundColor Yellow
    } else {
        Write-Host "[WARN] $backendExample not found. Create $backendEnv manually." -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] $backendEnv already exists, skipping." -ForegroundColor Gray
}

# --- Frontend .env ---
$frontendEnv = "frontend\.env"
$frontendExample = "frontend\.env.example"

if (-not (Test-Path $frontendEnv)) {
    if (Test-Path $frontendExample) {
        Copy-Item $frontendExample $frontendEnv
        Write-Host "[OK] Created $frontendEnv from $frontendExample" -ForegroundColor Green
    } else {
        Write-Host "[WARN] $frontendExample not found. Create $frontendEnv manually." -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] $frontendEnv already exists, skipping." -ForegroundColor Gray
}

# --- Backend venv + deps ---
$backendVenv = "backend\.venv"
if (-not (Test-Path $backendVenv)) {
    Write-Host "[..] Creating Python virtual environment in backend/.venv ..." -ForegroundColor Cyan
    Push-Location backend
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Pop-Location
    Write-Host "[OK] Backend venv created and dependencies installed." -ForegroundColor Green
} else {
    Write-Host "[OK] Backend venv already exists, skipping." -ForegroundColor Gray
}

# --- Alembic migrations ---
Write-Host "[..] Running database migrations ..." -ForegroundColor Cyan
Push-Location backend
& .\.venv\Scripts\Activate.ps1
alembic upgrade head
Pop-Location
Write-Host "[OK] Migrations applied." -ForegroundColor Green

# --- Frontend node_modules ---
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "[..] Installing frontend dependencies ..." -ForegroundColor Cyan
    Push-Location frontend
    npm install
    Pop-Location
    Write-Host "[OK] Frontend dependencies installed." -ForegroundColor Green
} else {
    Write-Host "[OK] Frontend node_modules already exists, skipping." -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "1. Make sure PostgreSQL is running and backend/.env has the correct DATABASE_URL."
Write-Host "2. Start backend:  cd backend  ; .venv\Scripts\Activate.ps1 ; uvicorn app.main:app --reload"
Write-Host "3. Start frontend: cd frontend ; npm run dev"
