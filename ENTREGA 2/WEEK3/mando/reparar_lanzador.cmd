@echo off
rem Cambia el python.exe de .venv y .venv-gpu por el lanzador estandar de CPython.
rem uv crea los entornos con un lanzador propio sin firma, y Smart App Control de
rem Windows 11 lo bloquea a ratos («Una directiva de Control de aplicaciones bloqueo
rem este archivo»). El de CPython hace lo mismo y Windows lo deja ejecutar.
rem No toca ninguna directiva de seguridad. Guarda el original como *.uv-original.
setlocal
cd /d "%~dp0.."
for %%E in (.venv .venv-gpu) do call :reparar %%E
exit /b 0

:reparar
if not exist "%~1\pyvenv.cfg" (
  echo [--] %~1 no existe
  exit /b 0
)
set "BASE="
for /f "tokens=1,* delims==" %%A in ('findstr /b /c:"home" "%~1\pyvenv.cfg"') do set "BASE=%%B"
for /f "tokens=* delims= " %%A in ("%BASE%") do set "BASE=%%A"
set "NT=%BASE%\Lib\venv\scripts\nt"
if not exist "%NT%\python.exe" (
  echo [!!] %~1: no encuentro el lanzador de CPython en %NT%
  exit /b 1
)
for %%X in (python.exe pythonw.exe) do (
  if not exist "%~1\Scripts\%%X.uv-original" copy /y "%~1\Scripts\%%X" "%~1\Scripts\%%X.uv-original" >nul
  copy /y "%NT%\%%X" "%~1\Scripts\%%X" >nul
)
"%~1\Scripts\python.exe" -c "import sys; print('[OK] %~1:', sys.version.split()[0])"
exit /b 0
