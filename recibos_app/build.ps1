param(
    [string]$Name = "GeradorRecibos"
)

$ErrorActionPreference = "Stop"

if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $Name `
    --icon "assets\\icon.ico" `
    "main.py"

Write-Host "Build finalizado. Verifique a pasta dist/."
