# Start AI Railway Traffic Optimization Platform
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " AI RAILWAY TRAFFIC OPTIMIZATION & MANAGEMENT PLATFORM    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python 3.12+ was not found on PATH." -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Seeding Initial Database..." -ForegroundColor Yellow
python scripts/seed_database.py

Write-Host "[2/3] Validating AI Models & Neural Policies..." -ForegroundColor Yellow
python scripts/train_ai_models.py

Write-Host "[3/3] Launching FastAPI Operations Control Center..." -ForegroundColor Green
Write-Host "Dashboard URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Swagger Docs: http://localhost:8000/docs" -ForegroundColor Cyan

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
