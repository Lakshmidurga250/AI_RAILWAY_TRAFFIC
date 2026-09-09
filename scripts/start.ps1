# Windows PowerShell Startup Script for AI Railway Traffic System
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  Starting AI Railway Traffic Optimization & Control System" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# Check Python
$pythonVersion = python --version
Write-Host "[+] Detected $pythonVersion" -ForegroundColor Green

# Seed database
Write-Host "[*] Checking and seeding database..." -ForegroundColor Yellow
python scripts/seed_database.py

# Launch FastAPI server with Uvicorn
Write-Host "[*] Launching API server and Live Web Control Center at http://localhost:8000" -ForegroundColor Green
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
