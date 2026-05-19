# Phase 3: Citations & Scoring — Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement `citation_checker.py` — extract DOIs from the references section text, validate each against the CrossRef API, compute a citations score (0–10), and slot it into `layer_scores["citations"]` in `main.py`.

**What this phase does NOT include:**
- Gemini analysis (Phase 2 — complete)
- PDF report generation or frontend UI (Phase 4)
- Semantic Scholar API (out of scope — CrossRef only for MVP)

</domain>

<decisions>
## Implementation Decisions

### DOI Extraction
- **C-01:** **Strict match only** — extract DOIs only when preceded by an explicit label
  - Accepted prefixes: `DOI:`, `doi:`, `doi.org/`
  - Regex: `r'(?:doi\.org/|DOI:\s*|doi:\s*)(10\.\d{4,}/\S+)'`
  - Strip trailing punctuation (`.`, `,`, `)`) from captured DOI string
  - If no DOIs extracted → score = 0, issue = "No DOIs found in references section"
  - Do NOT attempt broad `10.\d{4,}/\S+` fishing — too many false positives from version numbers

### References Section Handling
- **C-02:** If `sections["references"]` is an empty string `""` (not detected by Phase 1 regex):
  - Return immediately: score = 0, issue = "No references section found in document"
  - Do NOT call CrossRef at all

### CrossRef Validation
- **C-03:** Validate each DOI against CrossRef REST API:
  - Endpoint: `GET https://api.crossref.org/works/{doi}`
  - Set header: `User-Agent: ResearchSense/1.0 (mailto:team@researchsense.dev)`
  - Timeout per request: 5 seconds
  - Three result states per DOI:
    - `verified` → HTTP 200
    - `not_found` → HTTP 404
    - `unreachable` → any other error (timeout, 5xx, connection error)
  - Validate DOIs sequentially (no async — keeps main.py clean)

### Score Calculation
- **C-04:** `citation_score = (verified_count / total_count) * 10`
  - `total_count` = all DOIs extracted (verified + not_found + unreachable)
  - Unreachable DOIs count against the score (not excluded)
  - Round to 1 decimal place
  - If CrossRef is completely unreachable for ALL DOIs → score = 0, issue = "Citation verification unavailable — CrossRef API unreachable"

### Integration Architecture
- **C-05:** `citation_checker.py` is a **standalone module** — not part of `gemini_analyzer.py`
  - Single public function: `check_citations(references_text: str) -> dict`
  - Called **sequentially** in `main.py` AFTER `gemini_analyzer.analyze_paper()` completes
  - Result overwrites `layer_scores["citations"]` placeholder (which starts at 0.0)
  - `scoring.calculate_score()` is called AFTER citation check — uses final merged scores
  - A CrossRef failure NEVER blocks the overall analysis — it just results in score 0

### main.py call order (locked)
```
1. pdf_parser.extract_text()
2. section_detector.detect_sections()
3. gemini_analyzer.analyze_paper(sections)       → layer_details + layer_scores (citations=0.0)
4. citation_checker.check_citations(sections["references"])  → overwrites layer_scores["citations"]
5. scoring.calculate_score(layer_scores)         → uses all 8 final scores
6. Return enriched JSON response
```

### Agent's Discretion
- Whether to use `requests` or `httpx` for HTTP calls (both are fine; `requests` is simpler)
- Exact timeout retry strategy (single attempt per DOI is fine for MVP)
- How many DOIs to cap extraction at (suggest max 20 to avoid excessive API calls)

### Future Scope (not in MVP)
- Semantic Scholar API for title-based citation lookup (no DOI papers)
- Parallel/async CrossRef requests for large reference lists
- Retraction Watch database check
- DOI title-matching verification (CrossRef response title vs reference text)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Prior Phase Contracts
- `.planning/phases/02-ai-analysis-engine/02-CONTEXT.md` — `layer_scores["citations"]` is the 0.0 placeholder this phase fills
- `scoring.py` — `WEIGHTS["citations"] = 0.10` — the weight citations carries in the final score
- `main.py` — integration point; step 4 in the call order above goes here

### Design Spec
- `desirable.md` — Citations section in report: "summary line + flagged/unverified DOIs only" — `not_found` DOIs are the ones shown in the report

### External API
- CrossRef REST API: `https://api.crossref.org/works/{doi}`
- No API key required for basic lookups
- Rate limit: 50 req/sec polite pool (with User-Agent header)

</canonical_refs>

<code_context>
## Integration Contract

### citation_checker.py output shape
```python
def check_citations(references_text: str) -> dict:
    """
    Returns:
    {
        "score": float,          # 0-10, rounded to 1 decimal
        "total_dois": int,       # total DOIs extracted
        "verified": int,         # HTTP 200 from CrossRef
        "not_found": int,        # HTTP 404 from CrossRef
        "unreachable": int,      # timeout / error
        "flagged_dois": [str],   # list of not_found DOI strings (shown in report)
        "issues": [str],         # for layer_details (report generator reads this)
        "suggestions": [str]     # for layer_details (report generator reads this)
    }
    """
```

### main.py additions (Phase 3)
```python
import citation_checker  # Phase 3

# After gemini_analyzer call:
citation_result = citation_checker.check_citations(sections.get("references", ""))
analysis["layer_scores"]["citations"] = citation_result["score"]
analysis["layer_details"]["citations"] = {
    "score": citation_result["score"],
    "issues": citation_result["issues"],
    "suggestions": citation_result["suggestions"],
}

# Pass citation_result to response (for report generator in Phase 4)
```

</code_context>

<specifics>
## Specific Ideas

- Cap DOI extraction at 20 per paper to avoid excessive CrossRef calls on large reference lists
- `flagged_dois` list feeds directly into Phase 4 report — only `not_found` DOIs are shown
- The `issues` list in the output should be human-readable sentences, e.g.:
  - "3 of 12 DOIs could not be verified (not found in CrossRef)"
  - "2 DOIs were unreachable during validation"

</specifics>

<deferred>
## Deferred Ideas

- **Semantic Scholar API** — Future scope. CrossRef only for MVP.
- **Async parallel CrossRef requests** — Future scope. Sequential is fine for MVP.
- **Retraction Watch** — Future scope. Not part of v1.
- **Title-matching verification** — Future scope. 200 OK = verified for MVP.

</deferred>

---

*Phase: 03-citations-scoring*
*Context gathered: 2026-05-19 via /gsd-discuss-phase 3*
