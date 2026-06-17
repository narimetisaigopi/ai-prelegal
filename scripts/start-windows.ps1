$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
docker compose up --build -d
Write-Output "Prelegal started at http://localhost:8000"
