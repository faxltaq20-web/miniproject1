@echo off
REM ============================================================
REM  ResearchSense — Phase 9 Debug Suite (Windows)
REM  Runs all 4 debug steps in sequence:
REM    1. Fetch papers from arXiv
REM    2. Run full pipeline (/analyze + /report)
REM    3. Validate outputs
REM    4. Generate summary report
REM ============================================================

echo.
echo ============================================================
echo   ResearchSense Phase 9 — Full Debug Suite
echo ============================================================
echo.

REM Step 1: Fetch Papers
echo [STEP 1/4] Fetching papers from arXiv...
echo.
python "%~dp0debug_fetch_papers.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Paper fetching failed! Aborting.
    exit /b 1
)

echo.
echo [STEP 2/4] Running full pipeline...
echo.
python "%~dp0debug_run_pipeline.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Pipeline runner failed! Aborting.
    exit /b 1
)

echo.
echo [STEP 3/4] Validating outputs...
echo.
python "%~dp0debug_validate_outputs.py"

echo.
echo [STEP 4/4] Generating summary report...
echo.
python "%~dp0debug_summary_report.py"

echo.
echo ============================================================
echo   Debug suite complete. See DEBUG_REPORT.md for details.
echo ============================================================
echo.
