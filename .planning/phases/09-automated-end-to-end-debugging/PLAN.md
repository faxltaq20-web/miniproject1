# Plan: Automated End-to-End Debugging

**Phase:** Phase 9: Automated End-to-End Debugging
**Status:** Planned
**Archetype:** Test Harness (Fetch → Run → Validate → Report)

---

## Plan 1: Real Paper Fetcher — arXiv & Semantic Scholar OA

Build `debug_fetch_papers.py` — a script that automatically downloads ≥5 diverse real academic PDFs from open-access sources covering different paper types (full research, review, short/2-page, medicine, social science).

### Tasks
- [ ] Create `MAIN_PROJECT/debug/` directory to hold all Phase 9 debug tooling.
- [ ] Create `MAIN_PROJECT/debug/debug_fetch_papers.py`:
  - **arXiv Fetcher:** Query arXiv API (`export.arxiv.org/api/query`) for papers in diverse categories:
    - CS (cs.LG — machine learning, large reference lists with DOIs)
    - Quantitative Biology (q-bio.BM — biomedical, structured sections)
    - Social Science (econ.GN — economics, no-DOI references common)
    - A known short/2-page paper (use `maxResults=1&search_query=ti:survey` for review paper)
    - A known preprint-only paper without a proper references section (edge case)
  - **Download logic:** Fetch each paper's PDF from `https://arxiv.org/pdf/<arxiv_id>.pdf` using `requests` with a 30s timeout. Save to `debug/papers/<category>_<arxiv_id>.pdf`.
  - **Metadata sidecar:** For each downloaded paper, write a JSON sidecar `<name>.meta.json` containing:
    - `source`: `"arxiv"`
    - `arxiv_id`: the paper ID
    - `category`: paper category (cs, bio, econ, etc.)
    - `title`: paper title from arXiv feed
    - `expected_sections`: list of sections expected based on category (e.g. `["abstract", "introduction", "methodology", "results", "conclusion", "references"]`)
    - `has_dois`: `true`/`false` flag from arXiv metadata
    - `expected_ref_count`: reference count if available in arXiv metadata, else `null`
  - **Hardcoded fallback list:** If arXiv API is rate-limited or unavailable, fall back to a hardcoded list of 5 known-good open-access arXiv IDs (one per category, pre-validated). This ensures the fetcher always produces output.
  - Output a `debug/papers/MANIFEST.json` listing all successfully downloaded papers with their metadata paths.

### Verification
- Running `python debug/debug_fetch_papers.py` downloads exactly 5 PDF files to `debug/papers/`.
- Each PDF is non-zero bytes (≥50KB).
- A valid `MANIFEST.json` is written listing all 5 papers.
- Each paper has a `.meta.json` sidecar with the required keys.

---

## Plan 2: Full Pipeline Runner — `/analyze` + `/report` per Paper

Build `debug_run_pipeline.py` — a script that starts (or connects to) the FastAPI server and sequentially runs each fetched paper through the **full** `/analyze` → `/report` pipeline, capturing all outputs and errors.

### Tasks
- [ ] Create `MAIN_PROJECT/debug/debug_run_pipeline.py`:
  - **Server health pre-check:** Before running papers, GET `http://localhost:8000/health`. If the server is not running, print a clear error with instructions to start it (`uvicorn main:app --reload`) and exit with code 1.
  - **Gemini API pre-check:** Parse the `/health` response — if `gemini.any_key_working` is `false`, print a specific error ("No Gemini API keys are working — cannot run live analysis") and exit with code 1.
  - **Paper loop:** For each PDF listed in `debug/papers/MANIFEST.json`:
    1. POST the PDF file as multipart form-data to `POST http://localhost:8000/analyze`
    2. Record: HTTP status code, response time (ms), full JSON response body, any exception
    3. If `/analyze` returned HTTP 200: POST the JSON response body to `POST http://localhost:8000/report`
    4. Record: HTTP status code for `/report`, response Content-Type (must be `application/pdf`), response size in bytes
    5. Save the raw `/analyze` JSON response to `debug/results/<paper_name>_analyze.json`
    6. Save the downloaded PDF report to `debug/results/<paper_name>_report.pdf` (if successful)
  - **Error capture:** Wrap each paper's full run in a try/except. Record any exception as `{"status": "exception", "error": "<message>"}` and continue to the next paper — never abort the full run.
  - **Raw results log:** Write a `debug/results/RAW_RESULTS.json` containing a list of per-paper run records:
    ```json
    {
      "paper": "cs_2301.12345",
      "analyze_status": 200,
      "analyze_time_ms": 12450,
      "report_status": 200,
      "report_size_bytes": 14032,
      "analyze_response": { ... },
      "error": null
    }
    ```

### Verification
- Running `python debug/debug_run_pipeline.py` (with server running) processes all 5 papers without crashing.
- `debug/results/RAW_RESULTS.json` exists and has exactly 5 entries.
- For each successful paper: a `_analyze.json` file and a `_report.pdf` file exist in `debug/results/`.
- Server-not-running case: script exits with code 1 and prints a clear error.

---

## Plan 3: Output Validator & Gap Analyzer — Schema + Completeness Checks

Build `debug_validate_outputs.py` — a script that reads `RAW_RESULTS.JSON` and runs a comprehensive set of validation checks against each `/analyze` response, comparing against the paper's metadata sidecar to detect gaps.

### Tasks
- [ ] Create `MAIN_PROJECT/debug/debug_validate_outputs.py`:
  - **Schema validator:** For each `/analyze` response, verify the JSON has all required top-level keys:
    - `filename`, `detected_sections`, `section_count`, `warnings`, `layer_scores`, `layer_details`, `final_score`, `grade`, `citation_result`
  - **Score range validator:** For each `layer_scores` entry:
    - Each layer score must be a number in `[0, 10]`
    - `final_score` must be in `[0, 100]`
    - `grade` must be one of: `"A — Excellent"`, `"B — Good"`, `"C — Needs Improvement"`, `"D — Poor"`, `"F — Very Poor"`
  - **Layer completeness validator:** For each key in `layer_details` (`structure_sections`, `clarity_writing`, `methodology_rigor`, `evidence_claims`, `citations`):
    - Must have `score` (number), `issues` (non-empty list), `suggestions` (non-empty list)
    - Flag layers where `issues` contains `"Analysis unavailable — LLM returned unparseable response."` (FALLBACK_RESULT hit)
    - Flag layers where `score == 0` AND the corresponding paper section was detected as present (indicates possible analysis failure)
  - **Section detection gap checker:** Cross-reference `detected_sections` against the paper metadata's `expected_sections`:
    - Flag any `expected_sections` entry that is completely absent from `detected_sections`
    - Record the gap as `{"gap_type": "missing_section", "section": "<name>", "expected": true, "detected": false}`
  - **Citation gap checker:**
    - If `citation_result.total_refs == 0` AND the paper's `.meta.json` has `expected_ref_count > 5`, flag as `{"gap_type": "citation_extraction_failure"}`
    - If `citation_result.verified == 0` AND `citation_result.total_refs > 0` AND `has_dois == true` (from meta), flag as `{"gap_type": "doi_extraction_failure"}`
  - **Report PDF validator:** Check `debug/results/<paper_name>_report.pdf`:
    - File must exist and be non-zero bytes (≥5000 bytes)
    - Must start with PDF magic bytes `%PDF` (read first 4 bytes)
  - **Per-paper validation record:** Produce a structured dict per paper:
    ```json
    {
      "paper": "cs_2301.12345",
      "schema_ok": true,
      "score_ranges_ok": true,
      "layer_details_ok": true,
      "fallback_layers": [],
      "section_gaps": [],
      "citation_gaps": [],
      "report_pdf_ok": true,
      "warnings": ["layer methodology_rigor returned score 0 despite section being present"],
      "status": "PASS"  // or "WARN" or "FAIL"
    }
    ```
    - `FAIL` = any schema error OR score out of range OR report PDF missing/broken
    - `WARN` = fallback layers hit OR section gaps OR citation gaps
    - `PASS` = all checks clean
  - Save all validation records to `debug/results/VALIDATION.json`.

### Verification
- Running `python debug/debug_validate_outputs.py` against the sample paper results produces `VALIDATION.json`.
- The existing `sample_paper.pdf` test case (which is known-good) receives `"status": "PASS"` or `"WARN"` (not `"FAIL"`).
- At least one section gap or citation gap is detected across the 5 diverse papers (confirming the detector actually works).
- A paper with a forced bad response (manually edited `_analyze.json` with a missing key) produces `"status": "FAIL"`.

---

## Plan 4: Summary Report Generator — Human-Readable Diagnostic Output

Build `debug_summary_report.py` — the final script that reads `VALIDATION.json` and `RAW_RESULTS.json` and generates a comprehensive, human-readable terminal summary **and** a markdown report file.

### Tasks
- [ ] Create `MAIN_PROJECT/debug/debug_summary_report.py`:
  - **Load inputs:** Read `debug/results/VALIDATION.json` and `debug/results/RAW_RESULTS.json`.
  - **Aggregate statistics:**
    - Total papers tested, PASS count, WARN count, FAIL count
    - Average `final_score` across all successful papers
    - Average `analyze_time_ms` (pipeline latency)
    - Total fallback layers hit across all papers (Gemini parse failures)
    - Total section gaps detected
    - Total citation gaps detected
  - **Terminal output (color-coded):**
    - Print a bordered header: `ResearchSense — Phase 9 Debug Summary`
    - Print per-paper rows with status emoji: ✅ PASS, ⚠️ WARN, ❌ FAIL
    - Print aggregate statistics table
    - Print a "Gaps & Issues" section listing all warnings and failures in detail
    - Print a final verdict: `ALL CLEAR` / `WARNINGS FOUND` / `FAILURES DETECTED`
  - **Markdown report:** Write `debug/DEBUG_REPORT.md` with:
    - Executive summary table (paper | score | grade | status | time)
    - Aggregate statistics
    - Detailed gaps section (section gaps, citation gaps, fallback layers)
    - Recommendations for each category of gap found:
      - Section gaps → suggest regex pattern improvements in `section_detector.py`
      - Citation gaps → suggest DOI pattern updates in `citation_checker.py`
      - Fallback layers → suggest Gemini prompt hardening in `gemini_analyzer.py`
    - Timestamp and run metadata
  - **Exit code:** Exit 0 if no FAILs, exit 1 if any paper has `status: "FAIL"`.
- [ ] Create `MAIN_PROJECT/debug/run_debug.bat` (Windows) and `MAIN_PROJECT/debug/run_debug.sh` (cross-platform):
  - Convenience scripts that run all 4 steps in sequence:
    ```
    python debug/debug_fetch_papers.py
    python debug/debug_run_pipeline.py
    python debug/debug_validate_outputs.py
    python debug/debug_summary_report.py
    ```
  - Print a clear status message between steps.

### Verification
- Running `python debug/debug_summary_report.py` after validation produces both terminal output and `DEBUG_REPORT.md`.
- `DEBUG_REPORT.md` is non-empty and contains a valid markdown table.
- Running `debug/run_debug.bat` with the server running executes all 4 steps and produces the full report end-to-end.
- Any paper with `status: "FAIL"` causes the script to exit with code 1.
