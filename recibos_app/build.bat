@echo off
set NAME=GeradorRecibos
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
python -m PyInstaller --noconfirm --clean --onefile --windowed --name %NAME% --icon assets\icon.ico main.py
echo Build finalizado. Verifique a pasta dist/.
