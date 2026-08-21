$ErrorActionPreference="Stop"
if(-not(Test-Path .env)){Copy-Item .env.example .env}
Write-Host "Starting MykoKnoks..." -ForegroundColor Green
docker compose up --build
