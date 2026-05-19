---
wave: 1
depends_on: []
files_modified:
  - citation_checker.py
  - main.py
  - requirements.txt
autonomous: true
requirements:
  - CITE-01
  - CITE-02
---

# Phase 3: Citations & Scoring — Plan

**Phase:** 03 — Citations & Scoring
**Owner:** Person 3
**Depends on:** Phase 2 (`gemini_analyzer.analyze_paper()` returns `layer_scores["citations"] = 0.0` placeholder)
**Goal:** Implement `citation_checker.py` — extract DOIs (strict match), validate via CrossRef API, compute a 0–10 citations score, slot it into the pipeline in `main.py`.

---

## Canonical References (READ BEFORE STARTING)

- `.planning/phases/03-citations-scoring/03-CONTEXT.md` — all design decisions (C-01 through C-05)
- `desirable.md` — citations section in report: summary line + `not_found` DOIs only
- `scoring.py` — `WEIGHTS["citations"] = 0.10` — confirms weight of this layer
- `main.py` lines 75–97 — shows exactly where Phase 3 inserts after Gemini call and before scoring
- `.planning/phases/02-ai-analysis-engine/02-CONTEXT.md` — `layer_scores["citations"]` integration contract

---

## must_haves (goal-backward verification)

- [ ] `citation_checker.py` exists and `check_citations(references_text: str) -> dict` is callable
- [ ] Strict regex `(?:doi\.org/|DOI:\s*|doi:\s*)(10\.\d{4,}/\S+)` is used — no broad pattern matching
- [ ] Empty references text → immediate return: score=0, issue="No references section found in document"
- [ ] Each DOI validated against `https://api.crossref.org/works/{doi}` with 5s timeout
- [ ] Three result states: `verified` (200), `not_found` (404), `unreachable` (error/timeout)
- [ ] Score = `round((verified / total) * 10, 1)` — unreachable counts against score
- [ ] `flagged_dois` list contains only `not_found` DOIs (for the Phase 4 report)
- [ ] `main.py` calls `citation_checker.check_citations()` AFTER `gemini_analyzer` and BEFORE `scoring.calculate_score()`
- [ ] `layer_scores["citations"]` is overwritten with the real score before `scoring.calculate_score()` is called
- [ ] `layer_details["citations"]` is populated with `score`, `issues`, `suggestions`
- [ ] `citation_result` returned in the JSON response (Phase 4 report generator needs `flagged_dois`)

---

## Task 1 — Create `citation_checker.py`

<read_first>
- `.planning/phases/03-citations-scoring/03-CONTEXT.md` (all decisions C-01 through C-05)
- `desirable.md` (Gemini Output Contract + Citations section of report)
- `scoring.py` (confirm `citations` key and weight)
</read_first>

<action>
Create `citation_checker.py` in the project root with the following exact implementation:

```python
import re
import requests

# Max DOIs to validate per paper — avoids excessive CrossRef calls on large reference lists
MAX_DOIS = 20

# Strict DOI pattern — only extract where an explicit label precedes the DOI
DOI_PATTERN = re.compile(
    r'(?:doi\.org/|DOI:\s*|doi:\s*)(10\.\d{4,}/\S+)',
    re.IGNORECASE
)

# Trailing punctuation to strip from captured DOI strings
TRAILING_JUNK = re.compile(r'[.,;:)\]>]+$')

CROSSREF_BASE = "https://api.crossref.org/works/{doi}"
HEADERS = {
    "User-Agent": "ResearchSense/1.0 (mailto:team@researchsense.dev)"
}
TIMEOUT = 5  # seconds per request


def _extract_dois(references_text: str) -> list:
    """Extract up to MAX_DOIS DOIs using strict prefix matching."""
    raw_matches = DOI_PATTERN.findall(references_text)
    cleaned = []
    seen = set()
    for doi in raw_matches:
        doi = TRAILING_JUNK.sub("", doi).strip()
        if doi and doi not in seen:
            seen.add(doi)
            cleaned.append(doi)
        if len(cleaned) >= MAX_DOIS:
            break
    return cleaned


def _validate_doi(doi: str) -> str:
    """
    Query CrossRef for a single DOI.
    Returns: "verified" | "not_found" | "unreachable"
    """
    url = CROSSREF_BASE.format(doi=doi)
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code == 200:
            return "verified"
        elif response.status_code == 404:
            return "not_found"
        else:
            return "unreachable"
    except requests.RequestException:
        return "unreachable"


def check_citations(references_text: str) -> dict:
    """
    Extract DOIs from references text and validate each against CrossRef.

    Args:
        references_text: raw text of the paper's references section.
                         Pass "" if section was not detected.

    Returns:
        {
            "score": float,          # 0-10, rounded to 1 decimal
            "total_dois": int,
            "verified": int,
            "not_found": int,
            "unreachable": int,
            "flagged_dois": [str],   # not_found DOIs only — shown in Phase 4 report
            "issues": [str],
            "suggestions": [str]
        }
    """
    # C-02: empty references section
    if not references_text.strip():
        return {
            "score": 0.0,
            "total_dois": 0,
            "verified": 0,
            "not_found": 0,
            "unreachable": 0,
            "flagged_dois": [],
            "issues": ["No references section found in document."],
            "suggestions": ["Add a References section with properly formatted citations including DOIs."],
        }

    # C-01: extract DOIs with strict matching
    dois = _extract_dois(references_text)

    if not dois:
        return {
            "score": 0.0,
            "total_dois": 0,
            "verified": 0,
            "not_found": 0,
            "unreachable": 0,
            "flagged_dois": [],
            "issues": ["No DOIs found in references section."],
            "suggestions": ["Include DOIs for all cited works to improve citation verifiability."],
        }

    # C-03: validate each DOI sequentially
    results = {doi: _validate_doi(doi) for doi in dois}

    verified_count   = sum(1 for s in results.values() if s == "verified")
    not_found_count  = sum(1 for s in results.values() if s == "not_found")
    unreachable_count = sum(1 for s in results.values() if s == "unreachable")
    total = len(dois)

    flagged_dois = [doi for doi, status in results.items() if status == "not_found"]

    # C-04: all unreachable → score 0, special issue message
    if unreachable_count == total:
        return {
            "score": 0.0,
            "total_dois": total,
            "verified": 0,
            "not_found": 0,
            "unreachable": unreachable_count,
            "flagged_dois": [],
            "issues": ["Citation verification unavailable — CrossRef API unreachable."],
            "suggestions": ["Retry the analysis when network access is available."],
        }

    # C-04: score = verified / total * 10 (unreachable counts against)
    score = round((verified_count / total) * 10, 1)

    # Build human-readable issues and suggestions
    issues = []
    suggestions = []

    if not_found_count > 0:
        issues.append(
            f"{not_found_count} of {total} DOI(s) could not be verified (not found in CrossRef)."
        )
        suggestions.append(
            "Check flagged DOIs for typos or confirm they are published in indexed journals."
        )
    if unreachable_count > 0:
        issues.append(
            f"{unreachable_count} of {total} DOI(s) were unreachable during validation."
        )
        suggestions.append(
            "Retry the analysis to attempt validation of unreachable DOIs."
        )
    if not issues:
        issues.append(f"All {total} DOI(s) verified successfully.")
        suggestions.append("No citation issues found.")

    return {
        "score": score,
        "total_dois": total,
        "verified": verified_count,
        "not_found": not_found_count,
        "unreachable": unreachable_count,
        "flagged_dois": flagged_dois,
        "issues": issues,
        "suggestions": suggestions,
    }
```

Key rules from CONTEXT.md to enforce:
- C-01: Only DOIs with explicit `doi.org/`, `DOI:`, or `doi:` prefix — no broad `10.\d+` scanning
- C-02: Empty string input → immediate return, no CrossRef call
- C-03: Validate sequentially (not async), 5s timeout, include `User-Agent` header
- C-04: Score formula is `(verified / total) * 10` — unreachable is NOT excluded from total
- C-04: All-unreachable → score 0, special "CrossRef API unreachable" issue message
</action>

<acceptance_criteria>
- `citation_checker.py` exists in project root
- `python -c "import citation_checker"` exits 0
- `citation_checker.py` contains `DOI_PATTERN` with strict prefix regex
- `citation_checker.py` contains `def check_citations(`
- `citation_checker.py` contains `def _extract_dois(`
- `citation_checker.py` contains `def _validate_doi(`
- `citation_checker.py` contains `MAX_DOIS = 20`
- Empty input test passes:
  ```bash
  python -c "
  import citation_checker
  r = citation_checker.check_citations('')
  assert r['score'] == 0.0
  assert r['total_dois'] == 0
  assert 'No references section found' in r['issues'][0]
  print('Empty input: PASS')
  "
  ```
- No-DOI input test passes:
  ```bash
  python -c "
  import citation_checker
  r = citation_checker.check_citations('Smith (2020). A paper without DOIs.')
  assert r['score'] == 0.0
  assert r['total_dois'] == 0
  assert 'No DOIs found' in r['issues'][0]
  print('No DOI input: PASS')
  "
  ```
- DOI extraction test passes (no network needed):
  ```bash
  python -c "
  import citation_checker
  text = 'LeCun et al. DOI: 10.1109/5.726791 and doi.org/10.48550/arXiv.1706.03762'
  dois = citation_checker._extract_dois(text)
  assert len(dois) == 2
  assert '10.1109/5.726791' in dois
  assert '10.48550/arXiv.1706.03762' in dois
  print('DOI extraction: PASS')
  "
  ```
</acceptance_criteria>

---

## Task 2 — Wire `citation_checker` into `main.py`

<read_first>
- `main.py` (current state — lines 75–97 show the Phase 2 Gemini call and scoring)
- `citation_checker.py` (just created — understand the return dict shape)
- `.planning/phases/03-citations-scoring/03-CONTEXT.md` (C-05 — locked call order)
</read_first>

<action>
Update `main.py` with the following changes:

1. Add import at top (after Phase 2 imports):
```python
import citation_checker  # Phase 3
```

2. Insert citation check AFTER the `gemini_analyzer` call and BEFORE `scoring.calculate_score()`.
Replace this existing block in `main.py`:

```python
        # Phase 2: Calculate weighted confidence score
        score_result = scoring.calculate_score(analysis["layer_scores"])
```

With:

```python
        # Phase 3: Run citation extraction and CrossRef validation
        citation_result = citation_checker.check_citations(sections.get("references", ""))

        # Phase 3: Overwrite citations placeholder with real score
        analysis["layer_scores"]["citations"] = citation_result["score"]
        analysis["layer_details"]["citations"] = {
            "score": citation_result["score"],
            "issues": citation_result["issues"],
            "suggestions": citation_result["suggestions"],
        }

        # Calculate weighted confidence score (now includes real citations score)
        score_result = scoring.calculate_score(analysis["layer_scores"])
```

3. Add `citation_result` to the return JSONResponse (after `"grade"`):
```python
            "citation_result": {
                "total_dois": citation_result["total_dois"],
                "verified": citation_result["verified"],
                "not_found": citation_result["not_found"],
                "unreachable": citation_result["unreachable"],
                "flagged_dois": citation_result["flagged_dois"],
            },
```

**Final call order in main.py after this task:**
1. `pdf_parser.extract_text()`
2. `section_detector.detect_sections()`
3. `gemini_analyzer.analyze_paper(sections)` — layer_scores["citations"] = 0.0
4. `citation_checker.check_citations(sections["references"])` — real score
5. Overwrite `layer_scores["citations"]` and `layer_details["citations"]`
6. `scoring.calculate_score(layer_scores)` — uses all 8 final scores
7. Return enriched JSON
</action>

<acceptance_criteria>
- `main.py` contains `import citation_checker`
- `main.py` contains `citation_checker.check_citations(`
- `main.py` contains `analysis["layer_scores"]["citations"] = citation_result["score"]`
- `main.py` contains `analysis["layer_details"]["citations"]`
- `scoring.calculate_score(` appears AFTER the `citation_result` assignment (grep line numbers confirm order)
- `main.py` contains `"citation_result"` in the return JSONResponse
- `python -c "import main"` exits 0
- Server starts: `uvicorn main:app` completes startup without error
</acceptance_criteria>

---

## Task 3 — Add `requests` to `requirements.txt`

<read_first>
- `requirements.txt` (current contents)
</read_first>

<action>
Add `requests` to `requirements.txt` if not already present.

Current `requirements.txt`:
```
google-genai
pymupdf
fastapi
uvicorn
python-dotenv
reportlab
```

Add `requests` on a new line. Final file:
```
google-genai
pymupdf
fastapi
uvicorn
python-dotenv
reportlab
requests
```

Then install: `pip install requests -q`
</action>

<acceptance_criteria>
- `requirements.txt` contains `requests` on its own line
- `pip show requests` exits 0
</acceptance_criteria>

---

## Verification

### Smoke tests (no network needed — run first)

```bash
# 1. Import check
python -c "import citation_checker, main; print('Imports OK')"

# 2. Empty references section
python -c "
import citation_checker
r = citation_checker.check_citations('')
assert r['score'] == 0.0 and r['total_dois'] == 0
assert 'No references section found' in r['issues'][0]
print('Empty section: PASS')
"

# 3. No DOIs in text
python -c "
import citation_checker
r = citation_checker.check_citations('Smith (2020). A paper. Journal of Things, 1(1), 1-10.')
assert r['score'] == 0.0 and r['total_dois'] == 0
assert 'No DOIs found' in r['issues'][0]
print('No DOIs: PASS')
"

# 4. DOI extraction (no network)
python -c "
import citation_checker
text = 'LeCun. DOI: 10.1109/5.726791\nVaswani. doi.org/10.48550/arXiv.1706.03762'
dois = citation_checker._extract_dois(text)
assert len(dois) == 2, f'Expected 2, got {len(dois)}: {dois}'
print('DOI extraction: PASS')
"

# 5. Broad pattern NOT matched (no explicit prefix)
python -c "
import citation_checker
text = 'version 10.3456/something in the text without doi prefix'
dois = citation_checker._extract_dois(text)
assert len(dois) == 0, f'Should be empty, got: {dois}'
print('Strict match enforced: PASS')
"
```

### UAT criteria (requires network — run after smoke tests pass)

1. POST a PDF with references to `/analyze` — response must include `citation_result` with `total_dois`, `verified`, `not_found`, `unreachable`, `flagged_dois`
2. `layer_details["citations"]` must be present in the response with `score`, `issues`, `suggestions`
3. `layer_scores["citations"]` must not be `0.0` if the paper has valid DOIs
4. `final_score` must reflect the real citations score (not the 0.0 placeholder)
5. POST a PDF with a broken DOI (`DOI: 10.9999/fake-doi-xxx`) — that DOI must appear in `flagged_dois`
