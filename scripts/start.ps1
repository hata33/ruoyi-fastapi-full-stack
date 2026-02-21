# A-FastAPI-Ry Development Startup Script

Write-Host "========================================" -ForegroundColor Green
Write-Host "    A-FastAPI-Ry Development Server" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

$projectRoot = Get-Location

# Start Backend
Write-Host "Starting backend server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$projectRoot\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app:app --reload --port 9099"

# Start Frontend
Write-Host "Starting frontend server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$projectRoot\frontend'; pnpm dev --port 5174"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Servers started successfully!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Two PowerShell windows opened. Close them to stop servers." -ForegroundColor Yellow