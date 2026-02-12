# ============================================================
# Build Script — GeradorRecibos
# Gera o executável .exe usando PyInstaller (--onefile --windowed)
# Uso: .\build.ps1
#      .\build.ps1 -Name "MeuApp"
# ============================================================

param(
    [string]$Name = "GeradorRecibos"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Preparando build de '$Name'..." -ForegroundColor Cyan

# Limpar artefatos anteriores
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# Executar PyInstaller
python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $Name `
    --icon "assets\icon.ico" `
    --add-data "assets\LOGO - MERCADO.png;assets" `
    --add-data "assets\icon.ico;assets" `
    "main.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host " ERRO: Build falhou!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Build finalizado com sucesso!" -ForegroundColor Green
Write-Host " Executavel: dist\$Name.exe" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
