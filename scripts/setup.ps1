# TürkResearcher — one-command local setup (Windows / PowerShell).
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
# Creates venv, installs deps, prepares .env, pulls the v2 index.
# Idempotent: re-running skips steps already done.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv")) {
    Write-Host "[setup] creating .venv" -ForegroundColor Cyan
    python -m venv .venv
}
$py = ".\.venv\Scripts\python.exe"

Write-Host "[setup] installing dependencies" -ForegroundColor Cyan
& $py -m pip install --quiet --upgrade pip
& $py -m pip install --quiet -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[setup] .env created from .env.example — EDIT IT: add DEEPSEEK_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host "[setup] .env already exists — leaving it" -ForegroundColor DarkGray
}

Write-Host "[setup] pulling v2 Chroma index (~13-15 GB, one time)" -ForegroundColor Cyan
& $py scripts\04_pull_index_from_hub.py --variant v2

Write-Host ""
Write-Host "[setup] DONE. Next:" -ForegroundColor Green
Write-Host "  1) .env icine DEEPSEEK_API_KEY=sk-... ekle (henuz eklemediysen)"
Write-Host "  2) $py app.py     ->  http://127.0.0.1:7860"
