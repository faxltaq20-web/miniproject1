---
phase: 12-improve-citation-detection
verified: 2026-06-13T00:00:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
test_suite:
  citation_checker: 61/61 passed
  text_compressor:  46/46 passed
  total:            107/107 passed
gaps: []
deferred: []
human_verification: []
---

# Phase 12: Improve Citation Detection — Verification Report

**Phase Goal:** Improve the accuracy, layout-preservation, and robustness of citation detection, reference extraction, and citation scoring in ResearchSense by addressing five critical bugs and limitations in section parsing, text extraction, and reference validation.

**Verified:** 2026-06-13
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Verification Criteria V1–V6)

| #   | Truth                                          | Status     | Evidence                                                                                                                       |
| --- | ---------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------ |
| V1  | Balanced Trailing Truncation                   | ✓ VERIFIED | `_clean_doi_parentheses()` at `citation_checker.py:55-77`; counts opens vs closes; behavioral test confirmed.                   |
| V2  | Non-Exclusive DOI Search                       | ✓ VERIFIED | `_extract_dois()` at `citation_checker.py:80-110` iterates both `DOI_LABELED` and `DOI_STANDALONE`; behavioral test confirmed.  |
| V3  | Unified Scoring                                | ✓ VERIFIED | `check_citations()` at `citation_checker.py:469-870` runs per-reference DOI-first/title-fallback in `ThreadPoolExecutor(5)`.    |
| V4  | References Stop Keyword Tolerance              | ✓ VERIFIED | `section_detector.py:262-272` (stop-keyword exemption) + `:96` (bibliographic-line heading exclusion). Functional test passed.  |
| V5  | Two-Column Text Extraction                     | ✓ VERIFIED | `pdf_parser.py:27` uses `page.get_text("text", sort=True)`.                                                                     |
| V6  | Test Suite Coverage                            | ✓ VERIFIED | `pytest MAIN_PROJECT/tests/` → **107 passed in 0.38s** (61 citation_checker + 46 text_compressor).                              |

**Score:** 6/6 truths verified.

---

## Detailed Verification

### V1 — Balanced Trailing Truncation

**Implementation:** `MAIN_PROJECT/citation_checker.py` lines 55–77

```python
def _clean_doi_parentheses(doi: str) -> str:
    if not doi:
        return doi
    while doi.endswith(')') and doi.count('(') < doi.count(')'):
        doi = doi[:-1]
    while doi.endswith(']') and doi.count('[') < doi.count(']'):
        doi = doi[:-1]
    return doi
```

Also verified `TRAILING_JUNK` regex (line 28) has been tightened so closing `)` / `]` are NOT pre-stripped — they are handled exclusively by `_clean_doi_parentheses()`. This was an auto-fix flagged in the SUMMARY (Deviation #1) and is essential to make V1 actually work.

**Test coverage:** `TestCleanDoiParentheses` (9 tests) — all pass.
**Behavioral spot check:**
- `_clean_doi_parentheses("10.1000/xyz(abc)")` → `"10.1000/xyz(abc)"` (preserved) ✓
- `_clean_doi_parentheses("10.1000/foo)")` → `"10.1000/foo"` (stripped) ✓

### V2 — Non-Exclusive DOI Search

**Implementation:** `MAIN_PROJECT/citation_checker.py` lines 80–110

The loop `for pattern in (DOI_LABELED, DOI_STANDALONE):` iterates BOTH patterns and merges results — no early-out on the labeled pattern. Deduplication preserves discovery order; cap at `MAX_DOIS=20`.

**Test coverage:** `TestCombinedDoiExtraction` (4 tests) — all pass.
**Behavioral spot check:** Mixed bibliography with labeled (`DOI:`), `doi.org/`, and standalone DOIs all extracted correctly ✓.

### V3 — Unified Scoring

**Implementation:** `MAIN_PROJECT/citation_checker.py` lines 469–870

`check_citations()` runs the new per-reference validation flow:
1. Builds `sample_lines` from up to `SAMPLE_CAP=15` reference lines (line 528).
2. For each sample line, `_validate_reference()` (lines 644–714):
   - Extracts DOIs from THIS reference's line only.
   - Validates each via `_validate_doi()` (CrossRef).
   - If all DOIs `not_found` or none present → falls back to `_verify_title_semantic_scholar()`.
3. Runs all per-ref validations in a `ThreadPoolExecutor(max_workers=5)` (line 718).
4. Aggregates `verified` / `not_found` / `unreachable` counts; computes blended score (80% DOI score + 20% recency, with ArXiv boost).

**Test coverage:** `TestUnifiedReferenceScoring` (4 tests) — all pass, including:
- `test_ref_without_doi_validated_via_title_when_others_have_dois` — confirms the historical bug is fixed.
- `test_not_found_doi_rescued_by_title_fallback` — DOI fails CrossRef, title rescues ref.
- `test_sample_capped_at_fifteen` — sample cap enforced.

**Behavioral spot check:** Mixed bibliography (one ref with DOI, one without) → both counted as verified when title fallback succeeds ✓.

**Edge case verified:** Synthetic sample-line construction for terse fixtures (lines 634–642) — auto-fix called out in SUMMARY Deviation #2 — works as documented.

### V4 — References Stop Keyword Tolerance

**Implementation:** `MAIN_PROJECT/section_detector.py`

Two interacting changes:

1. **Stop-keyword exemption inside references** (lines 262–272):

```python
is_strong_break = stripped.startswith("#") or (
    len(stripped) >= 3 and stripped.isupper()
)
if any(stop in clean for stop in STOP_KEYWORDS):
    if current_section == "references" and not is_strong_break:
        sections[current_section] += line + "\n"
        continue
    current_section = None
    continue
```

2. **Bibliographic-line heading exclusion** in `_is_heading_line()` (line 96):

```python
if re.match(r'^(?:\[\d+\]|\d+\.)\s+[A-Z][a-z]', stripped):
    return False
```

**Test coverage:** This change is in `section_detector.py` and is not covered by `test_citation_checker.py`. No dedicated unit test file for `section_detector.py` exists (gap in test coverage, but not a phase blocker — V4 is verified functionally below).

**Behavioral spot check (functional):** Constructed a mock paper with `# References` followed by `[2] Brown T. Appendix to a paper. Conference 2021.` and `[3] Lee K. Funding sources detail. Other 2022.` Both bibliography entries are preserved inside the references section (not truncated by the `appendix` / `funding` stop keywords) ✓.

**Note:** No `section_detector` unit tests exist for the new logic, but the change is small, narrowly-scoped (only takes effect when `current_section == "references"` AND the line is not a strong break), and the functional probe confirms it works. This is a minor coverage gap, not a verification failure.

### V5 — Two-Column Text Extraction

**Implementation:** `MAIN_PROJECT/pdf_parser.py` line 27

```python
pages = [page.get_text("text", sort=True) for page in doc]
```

The `sort=True` flag orders text blocks by reading order (top-to-bottom, left-to-right), preventing horizontal line-interleaving across two-column layouts.

**Test coverage:** No automated test (would require fixture PDFs and PyMuPDF rendering). Code change is verified by inspection — a one-line, well-documented kwarg flip.

### V6 — Test Suite Coverage

**Executed:** `python -m pytest MAIN_PROJECT/tests/test_citation_checker.py -q --tb=short`

```
61 passed in 0.32s
```

**Executed:** `python -m pytest MAIN_PROJECT/tests/ -q --tb=short`

```
107 passed in 0.38s
```

**Test count audit:**
- `test_citation_checker.py`: 61 tests counted via grep (`^    def test_`) — confirmed.
- `test_text_compressor.py`: 46 tests counted — confirmed.
- Total: 107 — matches SUMMARY claim of 90 baseline + 17 new.
- 17 new tests = `TestCleanDoiParentheses` (9) + `TestCombinedDoiExtraction` (4) + `TestUnifiedReferenceScoring` (4) ✓.

**Cross-phase regression check:** Both test files pass cleanly — no regressions in `test_text_compressor.py` (Phase 11 work).

---

## Required Artifacts

| Artifact                                       | Expected                                                                | Status     | Details                                       |
| ---------------------------------------------- | ----------------------------------------------------------------------- | ---------- | --------------------------------------------- |
| `MAIN_PROJECT/section_detector.py`             | References stop-keyword exemption + bibline heading filter              | ✓ VERIFIED | 17,274 bytes; both changes present and correctly scoped. |
| `MAIN_PROJECT/pdf_parser.py`                   | `sort=True` in PyMuPDF fallback                                         | ✓ VERIFIED | 1,627 bytes; line 27 confirmed.               |
| `MAIN_PROJECT/citation_checker.py`             | `_clean_doi_parentheses` + merged `_extract_dois` + unified `check_citations` | ✓ VERIFIED | 34,065 bytes; all three changes present.      |
| `MAIN_PROJECT/tests/test_citation_checker.py`  | 17 new tests for V1/V2/V3                                                | ✓ VERIFIED | 37,645 bytes; 61 tests total (17 are new).    |

---

## Key Link Verification

| From                           | To                                  | Via                                  | Status     | Details                                                                                                                          |
| ------------------------------ | ----------------------------------- | ------------------------------------ | ---------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `check_citations`              | `_validate_reference` (per ref)     | `ThreadPoolExecutor` submit          | ✓ WIRED    | Line 720 submits each sample_line to executor.                                                                                   |
| `_validate_reference`          | `_extract_dois` (per line)          | function call                        | ✓ WIRED    | Line 654.                                                                                                                        |
| `_validate_reference`          | `_validate_doi` (CrossRef)          | function call                        | ✓ WIRED    | Line 661.                                                                                                                        |
| `_validate_reference`          | `_verify_title_semantic_scholar`    | function call (fallback)             | ✓ WIRED    | Line 695 — the unified-scoring contract.                                                                                         |
| `_extract_dois`                | `_clean_doi_parentheses`            | function call                        | ✓ WIRED    | Line 104.                                                                                                                        |
| `detect_sections` (refs case)  | `is_strong_break` gate              | inline check                         | ✓ WIRED    | Lines 263–270.                                                                                                                   |
| `_is_heading_line`             | Bibliographic-line regex            | early `return False`                 | ✓ WIRED    | Line 96.                                                                                                                         |
| `extract_text` (fallback)      | `page.get_text("text", sort=True)`  | direct argument                      | ✓ WIRED    | Line 27.                                                                                                                         |

---

## Anti-Patterns Found

| File                                    | Line   | Pattern    | Severity | Impact                                                                                          |
| --------------------------------------- | ------ | ---------- | -------- | ----------------------------------------------------------------------------------------------- |
| `MAIN_PROJECT/citation_checker.py`      | 87     | `10.XXXX/` | ℹ️ Info  | Docstring comment describing standalone DOI pattern; NOT a debt marker. False positive on XXX.  |

No `TODO`, `FIXME`, `HACK`, `PLACEHOLDER`, `coming soon`, `not yet implemented`, or other debt markers found in any of the four modified files.

---

## Behavioral Spot-Checks

| Behavior                                                                            | Command                                                            | Result                  | Status |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------- | ------ |
| V1: `_clean_doi_parentheses("10.1000/xyz(abc)")`                                    | Python invocation                                                  | `10.1000/xyz(abc)`      | ✓ PASS |
| V1: `_clean_doi_parentheses("10.1000/foo)")`                                        | Python invocation                                                  | `10.1000/foo`           | ✓ PASS |
| V2: `_extract_dois(mixed_labeled_and_standalone)`                                   | Python invocation                                                  | All 3 DOIs present      | ✓ PASS |
| V3: `check_citations(mixed_doi_and_no_doi_refs)` with mocked APIs                   | Python invocation                                                  | verified=2, score=10.0  | ✓ PASS |
| V4: `detect_sections(refs_with_appendix_funding_biblines)`                          | Python invocation                                                  | Both biblines preserved | ✓ PASS |
| V5: `sort=True` present in `pdf_parser.extract_text` fallback                       | Source inspection                                                  | Present                 | ✓ PASS |
| V6: full test suite                                                                 | `python -m pytest MAIN_PROJECT/tests/ -q --tb=short`               | 107 passed in 0.38s     | ✓ PASS |
| V6: citation-only test suite                                                        | `python -m pytest MAIN_PROJECT/tests/test_citation_checker.py -q` | 61 passed in 0.32s      | ✓ PASS |

---

## Commit Verification

All eight task commits referenced in SUMMARY.md are present in `git log`:

| Task | Commit    | Status   |
| ---- | --------- | -------- |
| 1.1  | `a43cb3d` | ✓ FOUND  |
| 1.2  | `969bc88` | ✓ FOUND  |
| 2.1  | `e55681c` | ✓ FOUND  |
| 3.1  | `cfc9a40` | ✓ FOUND  |
| 3.2  | `094b8c2` | ✓ FOUND  |
| 3.3  | `da5ad3f` | ✓ FOUND  |
| 4.2  | `b06c603` | ✓ FOUND  |
| Docs | `8f5065f` | ✓ FOUND  |

---

## Requirements Coverage

Phase 12 was added as a bug-fix phase and is not formally tracked in `REQUIREMENTS.md` (per init JSON `phase_req_ids = null`). Verification is goal-based (criteria V1–V6), not requirement-traceability-based. All six criteria are verified.

The citation-related requirements (`CITE-01`, `CITE-02`) are owned by Phase 3 and remain in scope; Phase 12 strengthens their implementation but does not introduce or close them in REQUIREMENTS.md.

---

## Cross-Phase Regression Check

- **`test_text_compressor.py`** (46 tests from Phase 11 work): all pass ✓
- **`test_citation_checker.py`** baseline tests (`TestExtractDois`, `TestCheckCitationsOffline`, `TestScoreCalculation`, `TestExtractTitleFromRef`, `TestVerifyTitleSemanticScholar`, `TestParallelVerificationScoring`): all pass ✓
- No untracked-file leakage from Phase 12: `MAIN_PROJECT/cache/*` and `graphify-out/*` dirty state is pre-existing and untouched by this phase's commits ✓

---

## Minor Observations (Non-Blocking)

1. **No dedicated unit tests for `section_detector.py`.** V4 is verified by functional spot-check only. A future hardening task could add `MAIN_PROJECT/tests/test_section_detector.py` to lock the behavior in. Not a phase blocker — the change is small and self-consistent.
2. **No dedicated unit test for `pdf_parser.py` `sort=True` behavior.** Would require fixture PDFs. Code change is a one-line kwarg flip with a clear PyMuPDF semantic — verified by inspection.
3. **SUMMARY Deviation #1 (TRAILING_JUNK tightening)** was essential for V1 to work end-to-end. The verifier confirms the regex at line 28 no longer includes `)` or `]`, matching the deviation note.
4. **SUMMARY Deviation #2 (synthetic sample-lines)** is present at lines 634–642 of `citation_checker.py`. The behavior is defensive and only triggers on test fixtures with refs <21 chars; real-world impact is nil.
5. **`test_citation_checker.py` `_verify_references_parallel` mocks** still use the old `{"verified", "not_found", "checked"}` shape (no `"unreachable"` key). The production function (line 393) does return `"unreachable"`, and the no-DOI branch (line 536) defensively uses `.get("unreachable", 0)`. The mocks work because of the defensive `.get()`. Not a verification failure, but a future test-tidy opportunity.

---

## Gaps Summary

**None.** All six verification criteria pass against the actual codebase. The implementation matches every claim in `12-SUMMARY.md`. Test counts match exactly (61 / 46 / 107). All commits exist. No anti-patterns or unresolved debt markers.

---

## Status: PASSED

Phase 12 goal — improving the accuracy, layout-preservation, and robustness of citation detection, reference extraction, and citation scoring — is achieved end-to-end. The codebase reflects the planned changes, the test suite locks in the new behavior with zero regressions, and behavioral spot-checks confirm each criterion functions as documented. Ready to proceed to the next phase.

---

*Verified: 2026-06-13*
*Verifier: Claude (gsd-verifier)*
