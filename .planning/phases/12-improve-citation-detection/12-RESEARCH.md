# Phase 12 Research: Improve Citation Detection

This document compiles the research findings and proposed solutions for the citation detection and section parsing inefficiencies in ResearchSense.

---

## 1. Identified Issues

### A. Section Detection Truncation
In `section_detector.py`, bibliography lines containing keywords like `"appendix"`, `"supplementary"`, or `"funding"` (e.g. `[12] J. Smith, "A study of networks," Journal of AI, Appendix`) are misclassified as section headings. This triggers stop keyword logic, setting `current_section = None` and discarding the remainder of the references.

### B. Multi-Column Layout Scrambling
Plain PyMuPDF text extraction (`fitz.get_text()`) extracts text horizontally, scrambling bibliography entries in two-column layouts. Layout-aware sorting is required.

### C. Labeled vs. Standalone DOI Mutual Exclusion
In `citation_checker.py`, if a labeled DOI is found first, the standalone DOI pattern search is skipped entirely. Mixed-format bibliographies lose standalone DOIs.

### D. All-or-None Title Check
The presence of a single DOI disables title checking for the rest of the references. If that single DOI fails validation, the score drops to `0.0`, ignoring all other references.

### E. Trailing Junk Truncation
Trailing closing parentheses `)` or brackets `]` are stripped blindly from DOIs, which corrupts valid DOIs that end with balanced brackets (e.g., `10.1000/abc(123)`).

---

## 2. Technical Solutions

### A. Refined Section Detector (`section_detector.py`)
Prevent stop keyword triggers within the references section unless it is a strong section header (e.g. markdown `#` or all-caps). Modify `_is_heading_line()` to ignore standard bibliography list item formats.

### B. Column-Sorted PDF Extraction (`pdf_parser.py`)
Modify PyMuPDF fallback extraction to use coordinate sorting natively by passing `sort=True` to `page.get_text()`:
```python
pages = [page.get_text("text", sort=True) for page in doc]
```

### C. Combined Labeled & Standalone DOI Search (`citation_checker.py`)
Search both `DOI_LABELED` and `DOI_STANDALONE` patterns and merge the results:
```python
def _extract_dois(references_text: str) -> list:
    dois = []
    seen = set()
    for pattern in [DOI_LABELED, DOI_STANDALONE]:
        for m in pattern.finditer(references_text):
            doi = m.group(1)
            doi = TRAILING_JUNK.sub("", doi).strip()
            cleaned_doi = _clean_doi_parentheses(doi)
            if cleaned_doi and cleaned_doi not in seen:
                seen.add(cleaned_doi)
                dois.append(cleaned_doi)
            if len(dois) >= MAX_DOIS:
                break
    return dois
```

### D. Unified Reference Validation & Scoring (`citation_checker.py`)
Iterate over a sample of references (max 15 to avoid rate limits). For each reference, attempt DOI validation first; if missing or invalid, fallback to Semantic Scholar title search. Aggregate success ratio for a balanced confidence score.

### E. Balanced Brackets Cleaner (`citation_checker.py`)
Only strip trailing closing brackets if they exceed the count of opening brackets:
```python
def _clean_doi_parentheses(doi: str) -> str:
    while doi.endswith(')') and doi.count('(') < doi.count(')'):
        doi = doi[:-1]
    while doi.endswith(']') and doi.count('[') < doi.count(']'):
        doi = doi[:-1]
    return doi
```
