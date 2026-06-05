"""
debug_run_pipeline.py — Full pipeline runner for Phase 9 debugging.

Starts by checking server health + Gemini API availability, then
runs each fetched paper through POST /analyze → POST /report,
saving all outputs and timing data.
"""

import json
import os
import sys
import time
import requests

# Fix Windows CP1252 encoding for Unicode output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(__file__)
PAPERS_DIR = os.path.join(BASE_DIR, "papers")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
MANIFEST_PATH = os.path.join(PAPERS_DIR, "MANIFEST.json")
RAW_RESULTS_PATH = os.path.join(RESULTS_DIR, "RAW_RESULTS.json")

API_BASE = "http://localhost:8000"
ANALYZE_URL = f"{API_BASE}/analyze"
REPORT_URL = f"{API_BASE}/report"
HEALTH_URL = f"{API_BASE}/health"

ANALYZE_TIMEOUT = 120  # 2 minutes — Gemini can be slow on free tier
REPORT_TIMEOUT = 30


# ─── Pre-Flight Checks ───────────────────────────────────────────────────────

def check_server_health() -> dict:
    """Check if FastAPI server is running and healthy."""
    # Try up to 3 times with increasing timeouts
    for attempt in range(3):
        try:
            timeout = 10 + (attempt * 5)  # 10s, 15s, 20s
            resp = requests.get(HEALTH_URL, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            else:
                return None
        except requests.ConnectionError:
            if attempt < 2:
                import time as _t
                _t.sleep(2)
                continue
            return None
        except requests.RequestException:
            return None
    return None


def preflight_checks() -> bool:
    """Run pre-flight checks. Returns True if ready to proceed."""
    print("  [Pre-Flight] Checking server health...", flush=True)

    health = check_server_health()

    if health is None:
        print("\n  ✗ ERROR: FastAPI server is not running!", flush=True)
        print("    Start it with:", flush=True)
        print("      cd MAIN_PROJECT && uvicorn main:app --reload", flush=True)
        print("    Then re-run this script.\n", flush=True)
        return False

    print(f"    Server status: {health.get('status', 'unknown')}", flush=True)

    # Check Gemini API
    gemini = health.get("gemini", {})
    if not gemini.get("any_key_working", False):
        print("\n  ✗ ERROR: No Gemini API keys are working!", flush=True)
        print("    Cannot run live AI analysis.", flush=True)
        print("    Check your .env file for valid GEMINI_KEY_* entries.\n", flush=True)
        return False

    keys_loaded = gemini.get("gemini_keys_loaded", 0)
    model = gemini.get("model", "unknown")
    print(f"    Gemini: {keys_loaded} key(s) loaded, model: {model}", flush=True)

    # Check CrossRef
    crossref = health.get("crossref", {})
    print(f"    CrossRef: {crossref.get('status', 'unknown')}", flush=True)

    # Check Semantic Scholar
    ss = health.get("semantic_scholar", {})
    print(f"    Semantic Scholar: {ss.get('status', 'unknown')}", flush=True)

    print("  [Pre-Flight] All checks passed ✓\n", flush=True)
    return True


# ─── Pipeline Runner ──────────────────────────────────────────────────────────

def run_analyze(pdf_path: str, filename: str) -> dict:
    """
    POST a PDF to /analyze and return the result dict.
    Returns: {"status": int, "time_ms": int, "response": dict|None, "error": str|None}
    """
    start = time.time()
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (filename, f, "application/pdf")}
            resp = requests.post(ANALYZE_URL, files=files, timeout=ANALYZE_TIMEOUT)

        elapsed_ms = int((time.time() - start) * 1000)

        if resp.status_code == 200:
            return {
                "status": resp.status_code,
                "time_ms": elapsed_ms,
                "response": resp.json(),
                "error": None,
            }
        else:
            # Try to extract error message
            try:
                err_body = resp.json()
            except Exception:
                err_body = resp.text[:200]
            return {
                "status": resp.status_code,
                "time_ms": elapsed_ms,
                "response": None,
                "error": str(err_body),
            }

    except requests.Timeout:
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "status": 0,
            "time_ms": elapsed_ms,
            "response": None,
            "error": f"Request timed out after {ANALYZE_TIMEOUT}s",
        }
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "status": 0,
            "time_ms": elapsed_ms,
            "response": None,
            "error": str(e),
        }


def run_report(analyze_response: dict) -> dict:
    """
    POST analyze response JSON to /report and return result.
    Returns: {"status": int, "size_bytes": int, "content_type": str, "pdf_data": bytes|None, "error": str|None}
    """
    try:
        resp = requests.post(
            REPORT_URL,
            json=analyze_response,
            timeout=REPORT_TIMEOUT,
        )

        if resp.status_code == 200:
            return {
                "status": resp.status_code,
                "size_bytes": len(resp.content),
                "content_type": resp.headers.get("Content-Type", ""),
                "pdf_data": resp.content,
                "error": None,
            }
        else:
            try:
                err_body = resp.json()
            except Exception:
                err_body = resp.text[:200]
            return {
                "status": resp.status_code,
                "size_bytes": 0,
                "content_type": "",
                "pdf_data": None,
                "error": str(err_body),
            }

    except Exception as e:
        return {
            "status": 0,
            "size_bytes": 0,
            "content_type": "",
            "pdf_data": None,
            "error": str(e),
        }


# ─── Main Runner ──────────────────────────────────────────────────────────────

def run_pipeline():
    """
    Main entry point. Reads MANIFEST.json, runs each paper through
    /analyze → /report, and saves all results.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("=" * 60, flush=True)
    print("  ResearchSense — Phase 9 Pipeline Runner", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    # Pre-flight
    if not preflight_checks():
        sys.exit(1)

    # Load manifest
    if not os.path.exists(MANIFEST_PATH):
        print("  ✗ ERROR: No MANIFEST.json found!", flush=True)
        print("    Run debug_fetch_papers.py first.\n", flush=True)
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    papers = manifest.get("papers", [])
    if not papers:
        print("  ✗ ERROR: MANIFEST.json has no papers!", flush=True)
        sys.exit(1)

    print(f"  Found {len(papers)} papers to process.\n", flush=True)

    raw_results = []

    for i, paper_info in enumerate(papers, 1):
        name = paper_info["name"]
        pdf_file = paper_info["pdf_path"]
        pdf_path = os.path.join(PAPERS_DIR, pdf_file)
        title = paper_info.get("title", name)

        print(f"[{i}/{len(papers)}] {title[:55]}...", flush=True)
        print(f"   Paper: {pdf_file}", flush=True)

        record = {
            "paper": name,
            "title": title,
            "category": paper_info.get("category", "unknown"),
            "analyze_status": 0,
            "analyze_time_ms": 0,
            "report_status": 0,
            "report_size_bytes": 0,
            "analyze_response": None,
            "error": None,
        }

        # Check PDF exists
        if not os.path.exists(pdf_path):
            record["error"] = f"PDF file not found: {pdf_file}"
            print(f"   ✗ PDF not found: {pdf_file}", flush=True)
            raw_results.append(record)
            continue

        try:
            # Step 1: /analyze
            print(f"   ↳ POST /analyze ...", flush=True)
            analyze_result = run_analyze(pdf_path, pdf_file)
            record["analyze_status"] = analyze_result["status"]
            record["analyze_time_ms"] = analyze_result["time_ms"]

            if analyze_result["response"]:
                record["analyze_response"] = analyze_result["response"]
                print(f"   ✓ Analyze: HTTP {analyze_result['status']} "
                      f"({analyze_result['time_ms']}ms) — "
                      f"Score: {analyze_result['response'].get('final_score', '?')} "
                      f"({analyze_result['response'].get('grade', '?')})", flush=True)

                # Save analyze JSON
                analyze_json_path = os.path.join(RESULTS_DIR, f"{name}_analyze.json")
                with open(analyze_json_path, "w", encoding="utf-8") as f:
                    json.dump(analyze_result["response"], f, indent=2)

                # Step 2: /report
                print(f"   ↳ POST /report ...", flush=True)
                report_result = run_report(analyze_result["response"])
                record["report_status"] = report_result["status"]
                record["report_size_bytes"] = report_result["size_bytes"]

                if report_result["pdf_data"]:
                    report_pdf_path = os.path.join(RESULTS_DIR, f"{name}_report.pdf")
                    with open(report_pdf_path, "wb") as f:
                        f.write(report_result["pdf_data"])
                    print(f"   ✓ Report: HTTP {report_result['status']} "
                          f"({report_result['size_bytes']} bytes)", flush=True)
                else:
                    record["error"] = f"Report failed: {report_result['error']}"
                    print(f"   ⚠ Report failed: {report_result['error']}", flush=True)

            else:
                record["error"] = f"Analyze failed: {analyze_result['error']}"
                print(f"   ✗ Analyze failed (HTTP {analyze_result['status']}): "
                      f"{analyze_result['error']}", flush=True)

        except Exception as e:
            record["error"] = str(e)
            print(f"   ✗ Exception: {e}", flush=True)

        raw_results.append(record)

        # Pause between papers to respect Gemini rate limits
        if i < len(papers):
            print(f"   [Waiting 5s before next paper...]\n", flush=True)
            time.sleep(5)

    # Write RAW_RESULTS.json
    with open(RAW_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_results, f, indent=2)

    # Summary
    success_count = sum(1 for r in raw_results if r["analyze_status"] == 200)
    fail_count = len(raw_results) - success_count

    print(f"\n{'=' * 60}", flush=True)
    print(f"  PIPELINE COMPLETE", flush=True)
    print(f"  Processed: {len(raw_results)} papers", flush=True)
    print(f"  Success:   {success_count}", flush=True)
    print(f"  Failed:    {fail_count}", flush=True)
    print(f"  Results:   {RAW_RESULTS_PATH}", flush=True)
    print(f"{'=' * 60}\n", flush=True)


if __name__ == "__main__":
    run_pipeline()
