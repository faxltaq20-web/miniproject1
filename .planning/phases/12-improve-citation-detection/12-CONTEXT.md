# Phase 12: Improve Citation Detection - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning
**Source:** Research and code reviews

<domain>
## Phase Boundary
This phase resolves 5 key bugs and inefficiencies in section parsing, text extraction, and citation checking, ensuring robust reference validation and accurate scoring.

Deliverables:
- Coordinate-sorted plain text extraction fallback.
- Stop-keyword check exemption for references to prevent section truncation.
- Robust bibliographic line filter in heading detection.
- Combined labeled + standalone DOI extraction with no mutual exclusion.
- Blended reference scoring (max 15 sample size) combining DOI and title check fallbacks.
- Parentheses-aware trailing junk trimmer for DOIs.
</domain>

<decisions>
## Implementation Decisions

### Section Detector Heuristics
- Skip stop keyword triggers if `current_section == "references"`, unless the line starts with `#` (markdown) or is fully uppercase (strong section break).
- Filter out standard bibliography lines (e.g. starting with `[1]` or `1.`) inside `_is_heading_line()` to prevent false positive heading classifications.

### PDF Parsing
- Pass `sort=True` to `page.get_text()` inside the PyMuPDF plain text fallback to preserve columns in standard reading order.

### Citation Checker
- Update `_extract_dois()` to execute both `DOI_LABELED` and `DOI_STANDALONE` patterns and merge their matches.
- Count parentheses/brackets in `_clean_doi_parentheses()` and only strip trailing `)` or `]` if unmatched.
- Loop and validate each of up to 15 sample references using `ThreadPoolExecutor`: validate DOI first; fallback to title lookup if DOI fails/missing. Aggregate success ratio for the final score.
</decisions>

<canonical_refs>
## Canonical References
- `MAIN_PROJECT/section_detector.py`
- `MAIN_PROJECT/citation_checker.py`
- `MAIN_PROJECT/pdf_parser.py`
- `MAIN_PROJECT/tests/test_citation_checker.py`
</canonical_refs>

<specifics>
## Specific Ideas
- Cap Semantic Scholar and Crossref parallel lookups at 15 references per paper to ensure quick response times and prevent rate limit blocks.
</specifics>
