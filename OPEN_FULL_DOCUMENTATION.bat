@echo off
REM Tivan Dashboard — Team Briefing Launcher
REM Double-click this file to open the briefing in your default browser

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Path to the HTML briefing
set "BRIEFING_HTML=%SCRIPT_DIR%BRIEFING.html"

REM Check if the HTML file exists
if not exist "%BRIEFING_HTML%" (
    echo.
    echo ERROR: Could not find BRIEFING.html
    echo.
    echo Expected location: %BRIEFING_HTML%
    echo.
    echo Make sure you're running this file from the Drill Tracker directory.
    echo.
    pause
    exit /b 1
)

REM Open the HTML file in the default browser
echo.
echo Opening Tivan Dashboard Team Briefing...
echo.

start "" "%BRIEFING_HTML%"

REM Success message
timeout /t 2 /nobreak >nul
cls
echo.
echo ✓ Team Briefing opened in your default browser.
echo.
echo To view offline or print:
echo   1. File → Save As (to save as PDF or HTML)
echo   2. File → Print → "Print to PDF" for easy sharing
echo.
pause
