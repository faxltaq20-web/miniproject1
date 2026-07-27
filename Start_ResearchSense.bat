@echo off
title ResearchSense Launcher
color 0B
cls

echo ==========================================================
echo           RESEARCHSENSE — LOCAL WEB APP LAUNCHER          
echo ==========================================================
echo.
echo [1/3] Spinning up ResearchSense server...
echo.

:: Activate virtual environment if it exists
if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
)

:: Start the FastAPI server in a minimised background window.
:: It now serves BOTH the API and the frontend at http://127.0.0.1:8000
start "ResearchSense Server" /D "%~dp0MAIN_PROJECT" /min python -m uvicorn main:app --host 127.0.0.1 --port 8000

:: Give the server time to initialise and bind the port
echo     Waiting for server to initialise...
timeout /t 5 /nobreak >nul

echo [2/3] Opening ResearchSense in your browser...
echo.

:: Open the full app URL — served by FastAPI (not as a file://)
start "" "http://127.0.0.1:8000"

echo ==========================================================
echo [3/3] ResearchSense is running!
echo.
echo * App URL:     http://127.0.0.1:8000
echo * API Health:  http://127.0.0.1:8000/health
echo.
echo ----------------------------------------------------------
echo KEEP THIS WINDOW OPEN while using the application.
echo Press ANY KEY in this window to stop the server and exit.
echo ----------------------------------------------------------
echo.

pause >nul

echo.
echo Stopping server...
taskkill /fi "windowtitle eq ResearchSense Server*" /f >nul 2>&1
taskkill /im python.exe /fi "windowtitle eq ResearchSense*" /f >nul 2>&1

echo Done. Goodbye!
timeout /t 2 /nobreak >nul
exit
