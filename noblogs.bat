@echo off
setlocal enabledelayedexpansion

:: noblogs.bat - Lanceur Windows pour noblogs-backup-lite
:: Utilise l'assistant interactif (backup/wizard.py)
echo ===================================================
echo     NoBlogs Backup - Sauvegarde pour Windows
echo ===================================================
echo.

:: 1. Verifier que Python est installe
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python 3 n'est pas installe ou n'est pas dans le PATH.
    echo.
    echo Veuillez telecharger et installer Python depuis le Microsoft Store
    echo ou depuis https://www.python.org/downloads/
    echo Assurez-vous de cocher "Add python.exe to PATH" lors de l'installation.
    echo.
    pause
    exit /b 1
)

:: 2. Configurer l'environnement virtuel (.venv)
set VENV_DIR=%~dp0.venv
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [INFO] Premiere utilisation : preparation de l'environnement ^(1 a 2 min^)...
    python -m venv "%VENV_DIR%"
    if !errorlevel! neq 0 (
        echo [ERREUR] Impossible de creer l'environnement virtuel.
        pause
        exit /b 1
    )

    echo [INFO] Installation des dependances...
    "%VENV_DIR%\Scripts\python.exe" -m pip install -q --upgrade pip
    "%VENV_DIR%\Scripts\python.exe" -m pip install -q -r "%~dp0requirements.txt"
    if !errorlevel! neq 0 (
        echo [ERREUR] Echec de l'installation des dependances.
        pause
        exit /b 1
    )
    type nul > "%VENV_DIR%\.reqs_installed"
    echo [OK] Environnement pret.
    echo.
)

if not exist "%VENV_DIR%\.reqs_installed" (
    "%VENV_DIR%\Scripts\python.exe" -m pip install -q -r "%~dp0requirements.txt" >nul 2>&1
    type nul > "%VENV_DIR%\.reqs_installed"
)

:: 3. Lancer l'assistant interactif
set PYTHONUTF8=1
set NOBLOGS_VENV=%VENV_DIR%
cd /d "%~dp0"
"%VENV_DIR%\Scripts\python.exe" -m backup wizard %*

echo.
pause
