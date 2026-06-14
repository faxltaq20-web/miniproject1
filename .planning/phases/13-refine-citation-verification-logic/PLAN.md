# Phase 13: Refine Citation Verification Logic — PLAN.md

**Phase Goal:** Refine the reference validation loop in `citation_checker.py` to eliminate bibliography sampling bias (by sweeping the entire references block for DOIs) and prevent API rate limits (by capping Semantic Scholar title searches to a maximum of 5).

---

## Context

### Affected Files
| File | Role |
|:---|:---|
| `MAIN_PROJECT/citation_checker.py` | Extracts DOIs, validates references against CrossRef and Semantic Scholar, and calculates citation scores. |
| `MAIN_PROJECT/tests/test_citation_checker.py` | Contains the unit tests for citation checking. |

---

## Execution Plan

### Plan 1: Citation Checker scoring & loop refactor (`citation_checker.py`)
**Goal:** Modify `check_citations()` to implement global DOI sweep and capped title verification fallback.

- [ ] **1.1** Update `check_citations()` in `citation_checker.py`:
  - Extract DOIs from the *entire* references section text (`dois = _extract_dois(references_text)`), capped at `MAX_DOIS = 20`.
  - Validate all extracted DOIs in parallel using `ThreadPoolExecutor` (5 workers).
  - Identify reference lines that did not have any DOI or where the DOI failed validation (`not_found`).
  - From this set of unverified references, select a sample of up to **max 5 references**.
  - Perform parallel Semantic Scholar title searches for this sample set.
  - Calculate `verified_count` as the sum of verified DOIs and verified titles.
  - Compute the blended score using the sum of checked DOIs and checked titles as the scorable base.
  - Ensure the API return dict format is preserved for all keys.

---

### Plan 2: Verification and Unit Testing (`tests/`)
**Goal:** Verify all changes against existing unit tests and add new tests covering the edge cases.

- [ ] **2.1** Run the existing test suite:
  - `pytest MAIN_PROJECT/tests/`
  - Confirm all 107 existing tests pass.
- [ ] **2.2** Add new tests to `test_citation_checker.py`:
  - Test global DOI extraction on a references list with DOIs located beyond the first 15 lines.
  - Test Semantic Scholar fallback query limit (asserting it never exceeds 5 queries).
  - Test blended score calculations with mixed DOIs and titles.
- [ ] **2.3** Run the full project test suite to verify zero regressions.

---

## Verification Criteria

| ID | Alignment | Pass Condition |
|:---|:---|:---|
| **V1** | Global DOI Sweep | DOIs located anywhere in a long references section (up to 20) are extracted and verified. |
| **V2** | Bounded Title Fallback | Fallback Semantic Scholar queries are capped at a maximum of 5, preventing rate limits. |
| **V3** | Blended Scoring | Citations score aggregates both DOI verifications and title fallback verifications. |
| **V4** | Test Suite Integrity | All existing and new tests pass (107 baseline + new tests). |
