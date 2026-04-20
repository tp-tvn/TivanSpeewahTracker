@echo off
title Tivan Dashboard — Install / Update
echo.
echo ============================================================
echo   Tivan Dashboard — Dependency Installer
echo   Tivan Limited / Speewah Fluorite Project
echo ============================================================
echo.

REM ── Check Python is available ────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python was not found on this machine.
    echo.
    echo  Please install Python 3.10 or newer from:
    echo    https://www.python.org/downloads/
    echo.
    echo  Make sure to tick "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo  Python found:
python --version
echo.

REM ── Upgrade pip silently ─────────────────────────────────────
echo  Updating pip...
python -m pip install --upgrade pip --quiet
echo  Done.
echo.

REM ── Install from requirements.txt ────────────────────────────
echo  Installing required packages from requirements.txt...
echo  (This may take a minute on first run)
echo.
python -m pip install -r "%~dp0requirements.txt"

if errorlevel 1 (
    echo.
    echo  ERROR: One or more packages failed to install.
    echo  Check the output above for details.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   All packages installed successfully.
echo.
echo   To launch the dashboard, double-click:
echo     run.bat
echo ============================================================
echo.
pause
