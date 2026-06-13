# Phase 12: Improve Citation Detection — PLAN.md

**Phase Goal:** Improve the accuracy, layout-preservation, and robustness of citation detection, reference extraction, and citation scoring in ResearchSense by addressing five critical bugs and limitations in section parsing, text extraction, and reference validation.

---

## Context

### Affected Files
| File | Role |
|:---|:---|
| `MAIN_PROJECT/section_detector.py` | Detects headings, filters stop keywords, and segments paper sections. |
| `MAIN_PROJECT/pdf_parser.py` | Extracts text from PDFs using PyMuPDF (with fallback plain text extraction). |
| `MAIN_PROJECT/citation_checker.py` | Extracts DOIs, validates references against CrossRef and Semantic Scholar, and calculates citation scores. |
| `MAIN_PROJECT/tests/test_citation_checker.py` | Contains the unit tests for citation checking. |

---

## Execution Plan

### Plan 1: Section Detector Refinements (`section_detector.py`)
**Goal:** Prevent bibliography lines containing keywords (like "appendix" or "funding") from truncating the references section, and filter out bibliographic lines from heading detection.

- [ ] **1.1** Modify `detect_sections()` in `section_detector.py`:
  - When `current_section == "references"`, skip stop keyword boundary checks unless the line is a markdown header (starts with `#`) or is fully uppercase (strong section break).
- [ ] **1.2** Modify `_is_heading_line()` in `section_detector.py`:
  - Ignore lines that match a bibliographic pattern (e.g., starts with `[1]` or `1.`) followed by title-case words, ensuring these lines are not falsely classified as section headings.

---

### Plan 2: Column-Sorted PDF Extraction (`pdf_parser.py`)
**Goal:** Preserve column flow in plain PyMuPDF extraction fallback to prevent scrambled reference text.

- [ ] **2.1** Update the PyMuPDF fallback in `extract_text()` in `pdf_parser.py`:
  - Use `page.get_text("text", sort=True)` instead of `page.get_text()` to sort text blocks by reading order (vertical then horizontal layout blocks).

---

### Plan 3: Citation Checker Revisions (`citation_checker.py`)
**Goal:** Implement combined labeled/standalone DOI extraction, balanced-brackets trailing junk trimming, and a unified parallel reference validation loop.

- [ ] **3.1** Create a helper function `_clean_doi_parentheses(doi: str) -> str` in `citation_checker.py` that counts open/close parentheses/brackets and only strips trailing `)` or `]` if they are unmatched.
- [ ] **3.2** Modify `_extract_dois()` in `citation_checker.py`:
  - Search both `DOI_LABELED` and `DOI_STANDALONE` patterns and merge their matches.
  - Call `_clean_doi_parentheses()` on each match, deduplicate, and return the combined list.
- [ ] **3.3** Update `check_citations()` in `citation_checker.py` to use a unified reference-by-reference validation:
  - Select up to 15 references as a sample to check.
  - Query each in parallel using `ThreadPoolExecutor` (5 workers).
  - For each reference line: extract and validate DOIs first; if DOIs are missing or invalid, fallback to Semantic Scholar title search.
  - Aggregate the verified ratio of checked references into a blended base score, maintaining existing ArXiv boost and recency scoring logic.

---

### Plan 4: Verification and Unit Testing (`tests/`)
**Goal:** Verify all changes against existing unit tests and add new tests covering the edge cases.

- [ ] **4.1** Run the existing test suite:
  - `pytest MAIN_PROJECT/tests/test_citation_checker.py`
  - Confirm all 90 existing tests pass.
- [ ] **4.2** Add new tests to `test_citation_checker.py`:
  - Test `_clean_doi_parentheses()` with balanced parentheses (e.g. `10.1000/xyz(abc)`) and unmatched ones (e.g. `10.1000/xyz(abc)`).
  - Test combined DOI extraction with mixed labeled and standalone DOIs.
  - Test unified scoring logic with a mix of references (some with valid DOIs, some with invalid DOIs, some without DOIs).
- [ ] **4.3** Run the full project test suite to verify zero regressions.

---

## Verification Criteria

| ID | Criterion | Pass Condition |
|:---|:---|:---|
| **V1** | Balanced Trailing Truncation | DOIs ending in balanced parentheses (e.g., `(abc)`) are preserved; unmatched closing characters are stripped. |
| **V2** | Non-Exclusive DOI Search | Labeled and standalone DOIs present in the same bibliography are both successfully extracted. |
| **V3** | Unified Scoring | References without DOIs are validated via Semantic Scholar title search even if other references in the paper have DOIs. |
| **V4** | References Stop Keyword Tolerance | Bibliographies containing the word "appendix" or "funding" are not truncated. |
| **V5** | Two-Column Text Extraction | PyMuPDF fallback preserves columns sequentially (no horizontal line merging). |
| **V6** | Test Suite Coverage | All existing + new unit tests pass successfully. |
