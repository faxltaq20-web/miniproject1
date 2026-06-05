@echo off
setlocal enabledelayedexpansion
title ResearchSense - Environment Setup
color 0B
cls

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║        RESEARCHSENSE — ONE-CLICK ENVIRONMENT SETUP         ║
echo  ║  Installs Python packages, creates venv, configures .env   ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

:: ─────────────────────────────────────────────────────────────────
:: STEP 0 — Resolve project root (where this script lives)
:: ─────────────────────────────────────────────────────────────────
set "PROJECT_ROOT=%~dp0"
:: Remove trailing backslash
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo  [0/6] Project root: %PROJECT_ROOT%
echo.

:: ─────────────────────────────────────────────────────────────────
:: STEP 1 — Check Python is installed
:: ─────────────────────────────────────────────────────────────────
echo  [1/6] Checking Python installation...

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo  ╔══════════════════════════════════════════════════════════╗
    echo  ║  ERROR: Python is NOT installed or not in PATH.         ║
    echo  ║                                                        ║
    echo  ║  Please install Python 3.10+ from:                     ║
    echo  ║  https://www.python.org/downloads/                     ║
    echo  ║                                                        ║
    echo  ║  IMPORTANT: Check "Add Python to PATH" during install. ║
    echo  ╚══════════════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)

:: Grab Python version string
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VERSION=%%v"
echo        Found Python %PY_VERSION%

:: Check minimum version (3.10+)
for /f "tokens=1,2 delims=." %%a in ("%PY_VERSION%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)
if !PY_MAJOR! lss 3 (
    echo        WARNING: Python 3.10+ is recommended. You have %PY_VERSION%.
) else if !PY_MINOR! lss 10 (
    echo        WARNING: Python 3.10+ is recommended. You have %PY_VERSION%.
) else (
    echo        Version OK ✓
)
echo.

:: ─────────────────────────────────────────────────────────────────
:: STEP 2 — Check pip
:: ─────────────────────────────────────────────────────────────────
echo  [2/6] Checking pip...

python -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo        pip not found. Attempting to bootstrap pip...
    python -m ensurepip --upgrade
    if %ERRORLEVEL% neq 0 (
        echo  ERROR: Could not install pip. Please install it manually.
        pause
        exit /b 1
    )
)
echo        pip is available ✓
echo.

:: ─────────────────────────────────────────────────────────────────
:: STEP 3 — Create virtual environment
:: ─────────────────────────────────────────────────────────────────
echo  [3/6] Setting up virtual environment...

set "VENV_DIR=%PROJECT_ROOT%\venv"

if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo        Virtual environment already exists at: venv\
    echo        Reusing existing environment.
) else (
    echo        Creating virtual environment at: venv\
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% neq 0 (
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo        Virtual environment created ✓
)

:: Activate the virtual environment
call "%VENV_DIR%\Scripts\activate.bat"
echo        Activated venv ✓
echo.

:: ─────────────────────────────────────────────────────────────────
:: STEP 4 — Upgrade pip inside venv & install dependencies
:: ─────────────────────────────────────────────────────────────────
echo  [4/6] Installing Python dependencies...
echo        Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

echo.
echo        Installing packages from requirements.txt...
echo        ─────────────────────────────────────────────
python -m pip install -r "%PROJECT_ROOT%\MAIN_PROJECT\requirements.txt"
if %ERRORLEVEL% neq 0 (
    echo.
    echo  ERROR: Dependency installation failed.
    echo  Try running manually:
    echo    cd "%PROJECT_ROOT%"
    echo    venv\Scripts\activate
    echo    pip install -r MAIN_PROJECT\requirements.txt
    pause
    exit /b 1
)
echo.
echo        All packages installed ✓
echo.

:: ─────────────────────────────────────────────────────────────────
:: STEP 5 — Set up .env configuration file
:: ─────────────────────────────────────────────────────────────────
echo  [5/6] Configuring environment variables...

set "ENV_FILE=%PROJECT_ROOT%\MAIN_PROJECT\.env"
set "ENV_EXAMPLE=%PROJECT_ROOT%\MAIN_PROJECT\.env.example"

if exist "%ENV_FILE%" (
    echo        .env file already exists — skipping.
    echo        Edit MAIN_PROJECT\.env to update your API keys.
) else (
    if exist "%ENV_EXAMPLE%" (
        copy "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
        echo        Created .env from .env.example ✓
        echo.
        echo  ╔══════════════════════════════════════════════════════════╗
        echo  ║  ACTION REQUIRED: Add your Gemini API key(s)           ║
        echo  ║                                                        ║
        echo  ║  Open: MAIN_PROJECT\.env                               ║
        echo  ║  Set:  GEMINI_KEY_1=your-api-key-here                  ║
        echo  ║                                                        ║
        echo  ║  Get a free key: https://aistudio.google.com/apikey    ║
        echo  ╚══════════════════════════════════════════════════════════╝
    ) else (
        echo        WARNING: .env.example not found. Creating minimal .env...
        (
            echo GEMINI_KEY_1=your-gemini-api-key-here
            echo GEMINI_KEY_2=
            echo GEMINI_KEY_3=
            echo GEMINI_KEY_4=
            echo GEMINI_KEY_5=
            echo GEMINI_MODEL=gemini-2.5-flash
            echo CONTACT_EMAIL=your-email@example.com
        ) > "%ENV_FILE%"
        echo        Created minimal .env ✓
        echo        IMPORTANT: Edit MAIN_PROJECT\.env with your Gemini API key.
    )
)
echo.

:: ─────────────────────────────────────────────────────────────────
:: STEP 6 — Verify installation
:: ─────────────────────────────────────────────────────────────────
echo  [6/6] Verifying installation...
echo.
echo        Checking core packages:

set "ALL_OK=1"

python -c "import google.genai; print('        ✓ google-genai')" 2>nul || (
    echo        ✗ google-genai — FAILED
    set "ALL_OK=0"
)

python -c "import pymupdf4llm; print('        ✓ pymupdf4llm')" 2>nul || (
    echo        ✗ pymupdf4llm — FAILED
    set "ALL_OK=0"
)

python -c "import fastapi; print('        ✓ fastapi')" 2>nul || (
    echo        ✗ fastapi — FAILED
    set "ALL_OK=0"
)

python -c "import uvicorn; print('        ✓ uvicorn')" 2>nul || (
    echo        ✗ uvicorn — FAILED
    set "ALL_OK=0"
)

python -c "import multipart; print('        ✓ python-multipart')" 2>nul || (
    echo        ✗ python-multipart — FAILED
    set "ALL_OK=0"
)

python -c "import reportlab; print('        ✓ reportlab')" 2>nul || (
    echo        ✗ reportlab — FAILED
    set "ALL_OK=0"
)

python -c "import requests; print('        ✓ requests')" 2>nul || (
    echo        ✗ requests — FAILED
    set "ALL_OK=0"
)

python -c "import dotenv; print('        ✓ python-dotenv')" 2>nul || (
    echo        ✗ python-dotenv — FAILED
    set "ALL_OK=0"
)

echo.

:: ─────────────────────────────────────────────────────────────────
:: FINAL SUMMARY
:: ─────────────────────────────────────────────────────────────────
echo  ════════════════════════════════════════════════════════════════
if "!ALL_OK!"=="1" (
    echo.
    echo  ╔══════════════════════════════════════════════════════════╗
    echo  ║            ✅  SETUP COMPLETED SUCCESSFULLY             ║
    echo  ╠══════════════════════════════════════════════════════════╣
    echo  ║                                                        ║
    echo  ║  To run the project:                                   ║
    echo  ║                                                        ║
    echo  ║  Option A — Double-click Start_ResearchSense.bat       ║
    echo  ║                                                        ║
    echo  ║  Option B — Manual:                                    ║
    echo  ║    1. Open a terminal in this folder                   ║
    echo  ║    2. venv\Scripts\activate                             ║
    echo  ║    3. cd MAIN_PROJECT                                  ║
    echo  ║    4. python main.py                                   ║
    echo  ║    5. Open frontend\index.html in your browser         ║
    echo  ║                                                        ║
    echo  ║  API Docs: http://localhost:8000/docs                  ║
    echo  ╚══════════════════════════════════════════════════════════╝
) else (
    echo.
    echo  ⚠  Some packages failed verification.
    echo     Try re-running this script or install manually:
    echo     pip install -r MAIN_PROJECT\requirements.txt
)
echo.
pause
endlocal
