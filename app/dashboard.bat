@echo off
REM Dashboard Launcher for Tivan Tracking Tool
REM This launches the main Streamlit dashboard app

cd /d "%~dp0"

echo.
echo ========================================
echo  TIVAN TRACKING TOOL - DASHBOARD
echo ========================================
echo.
echo Starting dashboard...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python and add it to your system PATH
    pause
    exit /b 1
)

REM Check if app.py exists
if not exist "app.py" (
    echo [ERROR] app.py not found in this directory
    echo Make sure you're in the correct folder
    pause
    exit /b 1
)

REM Launch the dashboard
python -m streamlit run app.py

pause
