#!/bin/bash
# ============================================================
#  ResearchSense — Phase 9 Debug Suite (Cross-Platform)
#  Runs all 4 debug steps in sequence:
#    1. Fetch papers from arXiv
#    2. Run full pipeline (/analyze + /report)
#    3. Validate outputs
#    4. Generate summary report
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "============================================================"
echo "  ResearchSense Phase 9 — Full Debug Suite"
echo "============================================================"
echo ""

# Step 1: Fetch Papers
echo "[STEP 1/4] Fetching papers from arXiv..."
echo ""
python "$SCRIPT_DIR/debug_fetch_papers.py"

echo ""
echo "[STEP 2/4] Running full pipeline..."
echo ""
python "$SCRIPT_DIR/debug_run_pipeline.py"

echo ""
echo "[STEP 3/4] Validating outputs..."
echo ""
python "$SCRIPT_DIR/debug_validate_outputs.py"

echo ""
echo "[STEP 4/4] Generating summary report..."
echo ""
python "$SCRIPT_DIR/debug_summary_report.py"

echo ""
echo "============================================================"
echo "  Debug suite complete. See DEBUG_REPORT.md for details."
echo "============================================================"
echo ""
