@echo off
REM Admin Panel Launcher for Tivan Tracking Tool
REM This launches the admin.py pre-authenticated admin panel

cd /d "%~dp0"

echo.
echo ========================================
echo  TIVAN TRACKING TOOL - ADMIN PANEL
echo ========================================
echo.
echo Starting admin panel...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python and add it to your system PATH
    pause
    exit /b 1
)

REM Check if admin.py exists
if not exist "admin.py" (
    echo [ERROR] admin.py not found in this directory
    echo Make sure you're in the correct folder
    pause
    exit /b 1
)

REM Launch the admin panel
python -m streamlit run admin.py

pause
