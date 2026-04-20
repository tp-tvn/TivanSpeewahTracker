@echo off
REM Drill Tracker Dashboard Launcher
REM Double-click this file to open the dashboard

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ═══════════════════════════════════════════════════════════════
echo        DRILL TRACKER DASHBOARD LAUNCHER
echo ═══════════════════════════════════════════════════════════════
echo.
echo Starting Drill Tracker Dashboard...
echo.
echo Opening browser at: http://localhost:8501
echo.
echo NOTE: Keep this window open while using the dashboard
echo Press Ctrl+C here to stop the dashboard
echo.
echo ───────────────────────────────────────────────────────────────
echo.

REM Run the Streamlit app
call app\dashboard.bat

REM If dashboard closes, show message
echo.
echo ═══════════════════════════════════════════════════════════════
echo Dashboard has stopped.
echo ═══════════════════════════════════════════════════════════════
echo.
echo To restart, double-click this file again: 🚀_OPEN_DASHBOARD.bat
echo.
pause
