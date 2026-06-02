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

:: Start the FastAPI backend server in a background window
start "ResearchSense Backend" /min python MAIN_PROJECT/main.py

:: Give the server 2 seconds to initialize and bind the port
timeout /t 3 /nobreak >nul

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
:: Taskkill the python window started by name
taskkill /fi "windowtitle eq ResearchSense Backend" /f >nul 2>&1

echo Done. Goodbye!
timeout /t 2 >nul
exit
