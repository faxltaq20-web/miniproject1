# Phase 7 — Output Consistency and Overall Refinement: PLAN

**Phase Goal:** Improve the consistency of LLM analysis outputs and refine all pipeline components and report outputs for production readiness.

---

## Plan 1: Deterministic Scoring & Few-Shot Prompting (OPT-01)

**Files:** `MAIN_PROJECT/gemini_analyzer.py`

### Tasks:
1. **Deterministic API Settings:** Update the API client generation call (`client.models.generate_content`) inside `gemini_analyzer.py` to enforce deterministic parameters:
   - Pass a `config` dictionary (or `genai.types.GenerateContentConfig`) with `temperature=0.0` and `top_p=0.95`.
2. **Anchored Few-Shot Prompting:** Refine the combined multi-layer analysis prompt in `gemini_analyzer.py` to include highly structured input/output examples (few-shot context):
   - Include a concise example paper abstract/intro block and the exact desired JSON response showing how to apply the 0-10 rubric to avoid score drift.
3. **Provider Standardization:** Ensure identical temperature and formatting parameters are passed if the client falls back to the OpenAI-compatible client.

### Verification:
- Run `python run_local.py sample_paper.pdf` three times consecutively.
- Confirm that the output scores for Structure, Clarity, Methodology, and Evidence layers are identical or vary by at most 0.1 points across all three runs.

---

## Plan 2: Parallel Citation Title Verification (OPT-04)

**Files:** `MAIN_PROJECT/citation_checker.py`, `MAIN_PROJECT/tests/test_citation_checker.py`

### Tasks:
1. **Title Extraction:** Implement a clean text extraction parser in `citation_checker.py` that isolates paper titles from bibliography lines lacking DOIs.
2. **Concurrent Fetching:** Integrate Python's `concurrent.futures.ThreadPoolExecutor` to send concurrent requests to Semantic Scholar's public API (`https://api.semanticscholar.org/graph/v1/paper/search?query={title}&limit=1`).
3. **Quota Protection (Sampling Cap):** Enforce a selective sampling limit: only query up to 10 references from the bibliography to keep API traffic low and avoid rate limits.
4. **String Similarity Check:** Implement a quick string similarity matcher to verify that the top Search response title matches our reference title. If verified, award full citation points.
5. **Calibrate Citation Scores:** Remove the strict 7.0/10 cap for zero-DOI papers. Allow papers with verified numbered bibliography references to earn up to a perfect **10.0** citation score.
6. **Update Tests:** Refine the pytest assertions in `tests/test_citation_checker.py` to cover the new parallel search logic and mock the Semantic Scholar responses.

### Verification:
- Run `pytest` to ensure all citation checker tests pass.
- Test citation checker on a paper with numbered references (like "Attention Is All You Need") and verify that a score above 7.0 is correctly achieved when references are authentic.

---

## Plan 3: PDF Spacing, Formatting & Safe Keeping (OPT-03)

**Files:** `MAIN_PROJECT/report_generator.py`

### Tasks:
1. **String Safeguard Helper:** Add a `_sanitize_and_truncate(text, max_len=135)` utility inside `report_generator.py`.
2. **Grid Overflow Budget:** In `_make_param_cell`, pass all issues and suggestions through the safeguard utility. This ensures dynamic LLM-generated sentences never exceed 135 characters and cause card grid misalignment.
3. **Cohesive Page Layout (Orphan Prevention):** Wrap key structural blocks inside ReportLab `KeepTogether` objects to ensure headers and their respective tables/cards never get separated:
   - Keep `Overall Score` header + `ScoreHero` together.
   - Keep `Detected Sections` header + pill grid together.
   - Keep `Multi-Layer Analysis` header + parameters grid together.
   - Keep `Citation Check` header + stats table + flagged table together.
   - Keep `Verdict` header + `VerdictCard` together.

### Verification:
- Generate a test PDF report using a paper with extremely long issue descriptions.
- Visually inspect the resulting PDF to verify that cards remain beautifully aligned and no orphaned headers appear at page breaks.

---

## Plan 4: API Pre-Flight & Health Checks (OPT-05)

**Files:** `MAIN_PROJECT/main.py`, `MAIN_PROJECT/gemini_analyzer.py`

### Tasks:
1. **Lightweight Connectivity Test:** Write a fast credentials verification function in `gemini_analyzer.py` that does a lightweight connectivity check.
2. **Fast Pre-Flight Guard:** Call this connectivity test at the very beginning of the `/analyze` POST route in `main.py`. If API credentials in `.env` are invalid or completely exhausted, return a fast HTTP 400 error immediately rather than waiting for slow network timeouts.
3. **FastAPI Diagnostics Endpoint:** Add a `GET /health` route in `main.py` that queries and returns the status of loaded Gemini keys, CrossRef connectivity, and Semantic Scholar availability in a structured JSON diagnostic format.

### Verification:
- Call `GET /health` via `curl` or browser and verify it returns a successful JSON diagnostic state.
- Set dummy keys in `.env`, trigger `/analyze` and check that it immediately throws a clear pre-flight failure message without performing text extraction.

---

## Execution Order

```
Plan 1 (Deterministic LLM & Few-Shot)  — foundational scoring accuracy
  ↓
Plan 2 (Parallel Citations Search)    — advanced bibliography verification
  ↓
Plan 3 (PDF Formatting Safeguards)    — visual layout polish
  ↓
Plan 4 (Diagnostics & Pre-Flight)     — operational safety & error recovery
```

**Estimated effort:** ~2 hours total
