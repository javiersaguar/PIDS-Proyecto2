@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" mando\preparar.py
if errorlevel 1 (
  echo Corrige los errores anteriores antes de conectar.
  pause
  exit /b 1
)
echo Abre http://127.0.0.1:8765 cuando arranque el servidor.
".venv\Scripts\python.exe" mando\servidor.py %*
