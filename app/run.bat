@echo off
cd /d "%~dp0"

:: Check Python is available
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed or could not be found.
    echo  Please install Python 3 from https://python.org and try again.
    echo.
    pause
    exit /b 1
)

echo Checking dependencies...
py -3 -m pip install -r requirements.txt --quiet

echo Starting Tivan Tracking Tool...

:: Open the browser after a short delay (runs silently in background)
start "" /b cmd /c "timeout /t 4 /nobreak >nul && start "" http://localhost:8501"

:: Run Streamlit in this window — close window to stop the server
py -3 -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false --server.headless true
