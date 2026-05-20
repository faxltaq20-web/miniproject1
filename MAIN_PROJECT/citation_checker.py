import re
import requests

# Max DOIs to validate per paper — avoids excessive CrossRef calls on large reference lists
MAX_DOIS = 20

# Strict DOI pattern — only extract where an explicit label precedes the DOI (C-01)
DOI_PATTERN = re.compile(
    r'(?:doi\.org/|DOI:\s*|doi:\s*)(10\.\d{4,}/\S+)',
    re.IGNORECASE
)

# Strip trailing punctuation that may be attached to a DOI in reference lists
TRAILING_JUNK = re.compile(r'[.,;:)\]>]+$')

CROSSREF_BASE = "https://api.crossref.org/works/{doi}"
HEADERS = {
    # Polite pool header — gives CrossRef rate-limit headroom (50 req/sec)
    "User-Agent": "ResearchSense/1.0 (mailto:team@researchsense.dev)"
}
TIMEOUT = 5  # seconds per request (C-03)


def _extract_dois(references_text: str) -> list:
    """
    Extract DOIs from references text using strict prefix matching only.
    Returns a deduplicated list of up to MAX_DOIS DOI strings.
    """
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
    Validate a single DOI against CrossRef REST API.

    Returns:
        "verified"    — HTTP 200 (DOI exists in CrossRef)
        "not_found"   — HTTP 404 (DOI not in CrossRef database)
        "unreachable" — timeout, connection error, or unexpected HTTP status
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
    Extract DOIs from the references section and validate each against CrossRef.

    Args:
        references_text: raw text of the paper's references section.
                         Pass "" if the section was not detected by section_detector.py.

    Returns:
        {
            "score": float,          # 0-10, rounded to 1 decimal
            "total_dois": int,
            "verified": int,
            "not_found": int,
            "unreachable": int,
            "flagged_dois": [str],   # not_found DOIs only — displayed in Phase 4 report
            "issues": [str],         # human-readable problem descriptions
            "suggestions": [str]     # human-readable fix recommendations
        }
    """
    # C-02: empty references section — no CrossRef call
    if not references_text.strip():
        return {
            "score": 0.0,
            "total_dois": 0,
            "verified": 0,
            "not_found": 0,
            "unreachable": 0,
            "flagged_dois": [],
            "issues": ["No references section found in document."],
            "suggestions": [
                "Add a References section with properly formatted citations including DOIs."
            ],
        }

    # C-01: strict DOI extraction
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
            "suggestions": [
                "Include DOIs for all cited works to improve citation verifiability."
            ],
        }

    # C-03: validate each DOI sequentially
    results = {doi: _validate_doi(doi) for doi in dois}

    verified_count    = sum(1 for s in results.values() if s == "verified")
    not_found_count   = sum(1 for s in results.values() if s == "not_found")
    unreachable_count = sum(1 for s in results.values() if s == "unreachable")
    total = len(dois)

    flagged_dois = [doi for doi, status in results.items() if status == "not_found"]

    # C-04 edge case: all DOIs unreachable — special message, score 0
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

    # C-04: score = verified / total * 10 (unreachable counts against score)
    score = round((verified_count / total) * 10, 1)

    # Build human-readable issues and suggestions
    issues = []
    suggestions = []

    if not_found_count > 0:
        issues.append(
            f"{not_found_count} of {total} DOI(s) could not be verified "
            f"(not found in CrossRef)."
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
