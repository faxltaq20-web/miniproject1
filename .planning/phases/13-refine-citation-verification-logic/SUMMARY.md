# Phase 13: Refine Citation Verification Logic — SUMMARY

**Status:** Implemented (pending user verification)
**Date:** 2026-06-14

## What changed

### `MAIN_PROJECT/citation_checker.py`
- Added module constant `MAX_TITLE_FALLBACK = 5`.
- Replaced the per-reference unified validation block in `check_citations()` with a Phase 13 two-stage flow:
  1. **Global DOI sweep.** All DOIs returned by `_extract_dois(references_text)` (already capped at `MAX_DOIS = 20`) are validated in parallel via `ThreadPoolExecutor(max_workers=5)`.
  2. **Capped title fallback.** Reference lines not covered by any verified DOI are collected; up to `MAX_TITLE_FALLBACK = 5` of them are sent in parallel to Semantic Scholar (`_verify_title_semantic_scholar`).
- Blended counts: `verified = verified_dois + verified_titles`, `not_found = not_found_dois + not_found_titles`, same for unreachable.
- Scoring base: `scorable = checked_dois + checked_titles` (excluding unreachable). Score formula and ArXiv boost preserved.
- Return-dict schema preserved exactly (`score`, `total_refs`, `verified`, `not_found`, `unreachable`, `arxiv_verified`, `flagged_dois`, `flagged_items`, `recency`, `issues`, `suggestions`).
- New issues string surfaces the title-fallback result: `"Title fallback: X/Y reference(s) verified via Semantic Scholar (capped at 5)."`

### `MAIN_PROJECT/tests/test_citation_checker.py`
- Updated three Phase 12 tests in `TestUnifiedReferenceScoring` whose assertions encoded the old per-reference contract (cap=15, single per-ref status combining DOI+title). They now assert the Phase 13 blended counts.
- Added new test class `TestPhase13GlobalSweep` with 3 tests:
  - `test_global_doi_extraction_finds_dois_beyond_line_fifteen` — V1
  - `test_semantic_scholar_fallback_capped_at_five` — V2
  - `test_blended_score_aggregates_dois_and_titles` — V3

## Test results

| Stage | Pass count |
|:---|:---|
| Baseline (pre-Phase-13) | 107 passed |
| After Plan 1 refactor + updated Phase 12 tests | 107 passed |
| After Plan 2 new tests | **110 passed** |

## Files modified

- `MAIN_PROJECT/citation_checker.py`
- `MAIN_PROJECT/tests/test_citation_checker.py`

## Commits

- `21df0de` feat(13-1): global DOI sweep + capped title fallback in check_citations
- `1023bec` test(13-2): add tests for global DOI sweep, title cap, blended score

## Deviations from PLAN.md

- **Three Phase 12 tests were updated, not just three new ones added.** PLAN.md said "Confirm all 107 existing tests pass." The semantic change in Plan 1 (DOIs and titles now scored separately, MAX_TITLE_FALLBACK=5 instead of per-line SAMPLE_CAP=15) made three Phase 12 assertions in `TestUnifiedReferenceScoring` obsolete:
  - `test_mixed_valid_and_invalid_dois_aggregate` — old expectation: `not_found == 1`; new: `2` (DOI + title both not_found).
  - `test_not_found_doi_rescued_by_title_fallback` — old expectation: DOI NOT in flagged_dois; new: it IS (DOIs reported separately from titles in Phase 13).
  - `test_sample_capped_at_fifteen` — old expectation: `verified <= 15`; new: `verified == 20` since global sweep validates all 20 DOIs.
  These tests were rewritten in place to assert the Phase 13 contract documented in `13-CONTEXT.md`. No deletion of assertions, just realignment.
- ArXiv verification and recency blending remained unchanged.
- The `if not dois:` legacy title-only branch was left intact (out of scope — only the DOIs-present unified branch was refactored).

## Verification (deferred to user)

V1, V2, V3, V4 from PLAN.md are covered by the new `TestPhase13GlobalSweep` class and the passing test suite, but the user has explicitly requested to verify the phase manually.
