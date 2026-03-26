Write-Host "Starting SAP O2C Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"cd backend; & '..\.venv\Scripts\activate.ps1'; uvicorn main:app --reload`""

Write-Host "Starting SAP O2C Frontend..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit -Command `"cd frontend; npm run dev`""

Write-Host "Servers are booting in separate windows." -ForegroundColor Yellow
Write-Host "1. Backend will be available at http://localhost:8000"
Write-Host "2. Frontend will be accessible at http://localhost:3000"
Write-Host "You can keep this window open or close it."
