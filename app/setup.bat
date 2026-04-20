@echo off
setlocal enabledelayedexpansion
title Tivan Dashboard - Setup

echo.
echo  ============================================================
echo    Tivan Dashboard - First Time Setup
echo  ============================================================
echo.

:: ── Step 1: Check for Python ─────────────────────────────────────────────────

set PYTHON=

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
    goto :python_found
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=py
    goto :python_found
)

:: Python not found — try installing via Windows Package Manager (winget)
echo  Python not found on this machine.
echo  Attempting to install Python automatically via winget...
echo  (This requires an internet connection and may take a minute)
echo.

winget --version >nul 2>&1
if %errorlevel% neq 0 (
    goto :no_winget
)

winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    goto :python_install_failed
)

echo.
echo  Python installed. Please close this window and re-run setup.bat
echo  (Windows needs to refresh its PATH before Python is recognised)
echo.
pause
exit /b 0

:no_winget
echo  Windows Package Manager (winget) is not available on this machine.
goto :python_install_failed

:python_install_failed
echo.
echo  ============================================================
echo    Could not install Python automatically.
echo.
echo    Please install Python manually:
echo    1. Go to https://www.python.org/downloads/
echo    2. Download the latest Python 3.x installer
echo    3. Run it and CHECK "Add Python to PATH"
echo    4. Re-run this setup.bat
echo  ============================================================
echo.
pause
exit /b 1

:python_found
echo  [OK] Python found:
%PYTHON% --version
echo.

:: ── Step 2: Upgrade pip ───────────────────────────────────────────────────────

echo  Updating pip...
%PYTHON% -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo  Warning: could not upgrade pip. Continuing anyway...
)
echo  [OK] pip ready
echo.

:: ── Step 3: Install all packages from requirements.txt ───────────────────────

if not exist requirements.txt (
    echo  ERROR: requirements.txt not found.
    echo  Make sure you are running this from the Tivan Tracking Tool folder.
    pause
    exit /b 1
)

echo  Installing required packages from requirements.txt...
echo  (This may take a few minutes on first run)
echo.
%PYTHON% -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo  ============================================================
    echo    One or more packages failed to install.
    echo    Check the error message above and try again.
    echo  ============================================================
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo    Setup complete! All packages installed successfully.
echo.
echo    To start the dashboard, run:  launch.bat
echo  ============================================================
echo.
pause
