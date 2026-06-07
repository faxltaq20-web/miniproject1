@echo off
title ResearchSense Launcher
color 0B
cls

echo ==========================================================
echo           RESEARCHSENSE WEB DASHBOARD LAUNCHER            
echo ==========================================================
echo.
echo [1/3] Spinning up FastAPI Backend Server in background...
echo.

:: Activate virtual environment if it exists
if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
)

:: Start the FastAPI backend server in a MINIMIZED background window.
:: Use /D to set working directory (avoids nested-quote bugs with spaces in path).
start "ResearchSense Backend" /D "%~dp0MAIN_PROJECT" /min python main.py

:: Give the server 5 seconds to initialize, import modules, and bind the port
echo     Waiting for server to initialize...
timeout /t 5 /nobreak >nul

echo [2/3] Opening Frontend Dashboard in your default browser...
echo.

:: Open index.html in the default browser
start "" "%~dp0frontend\index.html"

echo ==========================================================
echo [3/3] Application Launched Successfully!
echo.
echo * Backend API:  http://127.0.0.1:8000
echo * Frontend UI:  frontend/index.html (opened in browser)
echo.
echo ----------------------------------------------------------
echo KEEP THIS WINDOW OPEN while using the application.
echo Press ANY KEY in this window to stop the server and exit.
echo ----------------------------------------------------------
echo.

pause >nul

echo.
echo Stopping backend server...
:: Kill the python process that was started
taskkill /fi "windowtitle eq ResearchSense Backend*" /f >nul 2>&1
taskkill /im python.exe /fi "windowtitle eq ResearchSense*" /f >nul 2>&1

echo Done. Goodbye!
timeout /t 2 >nul
exit
