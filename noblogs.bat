@echo off
rem noblogs.bat - Lanceur Windows (double-clic) pour noblogs-backup.
rem L'assistant ("wizard") s'exécute en Python : sauvegarde puis republication
rem WordPress.com. Python 3 est requis (https://www.python.org/downloads/).
setlocal EnableDelayedExpansion
cd /d "%~dp0"

rem Forcer la sortie UTF-8 de la console (code page 65001)
chcp 65001 >nul

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo  [x] Python 3 n'est pas installe sur ce PC.
  echo.
  echo     1. Ouvrez https://www.python.org/downloads/
  echo     2. Installez Python ^(cochez "Add python.exe to PATH"^)
  echo     3. Relancez ce fichier.
  echo.
  pause
  exit /b 1
)

set "VENV=%CD%\.venv-win"
if not exist "%VENV%\Scripts\python.exe" (
  echo  [i] Premiere utilisation : preparation de l'environnement (1 a 2 min)...
  python -m venv "%VENV%"
  "%VENV%\Scripts\python.exe" -m pip install -q --upgrade pip
  "%VENV%\Scripts\python.exe" -m pip install -q -r requirements.txt
)

"%VENV%\Scripts\python.exe" -X utf8 -m backup wizard %*
set EXIT=%ERRORLEVEL%
echo.
if not "%EXIT%"=="0" (
  echo  [!] Fin avec erreur code %EXIT%.
)
pause
exit /b %EXIT%