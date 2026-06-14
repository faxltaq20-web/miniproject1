# Phase 13: Refine Citation Verification Logic - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning
**Source:** UAT and Report Analysis

<domain>
## Phase Boundary
This phase refines the reference verification loop in `citation_checker.py` to resolve the bibliography sampling bias and Semantic Scholar API rate limits (HTTP 429) observed on large bibliographies.

Deliverables:
- Global DOI extraction and validation from the entire references section (max 20 DOIs).
- Strictly bounded fallback title validation (max 5 references) for references without verified DOIs.
- Blended reference scoring aggregating verified DOIs and verified titles.
- Zero regressions on downstream consumers and test suite.
</domain>

<decisions>
## Implementation Decisions

### Citation Checker Scoring & Validation Loop
- Extract DOIs from the entire bibliography block, rather than restricting extraction to the first 15 lines.
- Validate all extracted DOIs (up to `MAX_DOIS = 20`) in parallel using `ThreadPoolExecutor` (5 workers).
- Identify references without DOIs (or references where DOIs failed). Select a sample of up to **5 references** from this set.
- Perform Semantic Scholar title searches *only* for this small sample of references, checking them in parallel. This preserves the title-based fallback check while guaranteeing we stay below the API rate limit.
- Calculate the score as: `verified = verified_dois + verified_titles`.
- Preserve the exact API return schema of `check_citations()` so that `scoring.py` and `report_generator.py` consume it without changes.
</decisions>

<canonical_refs>
## Canonical References
- `MAIN_PROJECT/citation_checker.py`
- `MAIN_PROJECT/tests/test_citation_checker.py`
</canonical_refs>

<specifics>
## Specific Ideas
- The sample cap of 5 for Semantic Scholar queries is a strict limit to prevent rate limits.
</specifics>
