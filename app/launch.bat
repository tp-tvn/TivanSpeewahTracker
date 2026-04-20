@echo off
title Tivan Dashboard

:: Detect python command
set PYTHON=
python --version >nul 2>&1
if %errorlevel% equ 0 (set PYTHON=python) else (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (set PYTHON=py)
)

if "%PYTHON%"=="" (
    echo  Python not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo    Starting Tivan Dashboard...
echo    Opening in your browser at http://localhost:8501
echo    Press Ctrl+C in this window to stop the app.
echo  ============================================================
echo.

%PYTHON% -m streamlit run app.py --server.headless false
