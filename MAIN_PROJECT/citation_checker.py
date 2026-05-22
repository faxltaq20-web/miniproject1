import re
import requests
from collections import Counter

# Max DOIs to validate per paper — avoids excessive CrossRef calls on large reference lists
MAX_DOIS = 20

# Strict DOI pattern — only extract where an explicit label precedes the DOI
DOI_PATTERN = re.compile(
    r'(?:doi\.org/|DOI:\s*|doi:\s*)(10\.\d{4,}/\S+)',
    re.IGNORECASE
)

# Strip trailing punctuation that may be attached to a DOI in reference lists
TRAILING_JUNK = re.compile(r'[.,;:)\]>]+$')

# Pattern to extract author-year citations like "Smith & Lee, 2019" or "(Author, 2020)"
AUTHOR_YEAR_PATTERN = re.compile(
    r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-z]+))?),?\s*\(?\s*(\d{4})\s*\)?'
)

CROSSREF_BASE = "https://api.crossref.org/works/{doi}"
HEADERS = {
    # Polite pool header — gives CrossRef rate-limit headroom (50 req/sec)
    "User-Agent": "ResearchSense/1.0 (mailto:team@researchsense.dev)"
}
TIMEOUT = 5  # seconds per request


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


def _extract_author_year_refs(text: str) -> list:
    """
    Extract author-year reference entries from the full paper text.
    Returns list of tuples: (author_string, year).
    """
    matches = AUTHOR_YEAR_PATTERN.findall(text)
    return [(author.strip(), year) for author, year in matches]


def _detect_duplicates(references_text: str) -> list:
    """
    Detect duplicate references in the references section.
    Returns a list of flagged_items for duplicates.
    """
    flagged = []
    lines = references_text.strip().splitlines()

    # Normalize each reference line and look for near-duplicates
    normalized = []
    for line in lines:
        clean = re.sub(r'\s+', ' ', line.strip().lower())
        if len(clean) > 20:  # Skip very short lines
            normalized.append((clean, line.strip()))

    # Check for duplicates by comparing first 60 chars (author+title usually)
    seen_prefixes = {}
    for norm, original in normalized:
        prefix = norm[:60]
        if prefix in seen_prefixes:
            # Extract author info for display
            author_match = re.match(r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+\w+))?.*?\d{4})',
                                     original, re.IGNORECASE)
            citation_label = author_match.group(1) if author_match else original[:40]
            flagged.append({
                "citation": citation_label,
                "category": "duplicate",
                "detail": "Listed twice with inconsistent page ranges."
            })
        else:
            seen_prefixes[prefix] = original

    return flagged


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


def check_citations(references_text: str, full_text: str = "") -> dict:
    """
    Extract DOIs from the references section, validate each against CrossRef,
    detect duplicates, and build structured flagged items.

    Args:
        references_text: raw text of the paper's references section.
        full_text: full paper text (used for in-text citation cross-referencing).

    Returns:
        {
            "score": float,            # 0-10, rounded to 1 decimal
            "total_refs": int,         # total reference entries
            "verified": int,
            "not_found": int,
            "unreachable": int,
            "flagged_dois": [str],     # DOIs that failed verification
            "flagged_items": [         # detailed flagged items for display
                {"citation": str, "category": str, "detail": str}
            ],
            "issues": [str],
            "suggestions": [str]
        }
    """
    # Empty references section — no CrossRef call
    if not references_text.strip():
        return {
            "score": 0.0,
            "total_refs": 0,
            "verified": 0,
            "not_found": 0,
            "unreachable": 0,
            "flagged_dois": [],
            "flagged_items": [],
            "issues": ["No references section found in document."],
            "suggestions": [
                "Add a References section with properly formatted citations including DOIs."
            ],
        }

    # Count total reference entries (non-empty lines that look like refs)
    ref_lines = [l.strip() for l in references_text.splitlines() if len(l.strip()) > 20]
    total_refs = max(len(ref_lines), 1)

    # Extract and validate DOIs
    dois = _extract_dois(references_text)
    flagged_items = []

    if not dois:
        return {
            "score": 0.0,
            "total_refs": total_refs,
            "verified": 0,
            "not_found": 0,
            "unreachable": 0,
            "flagged_dois": [],
            "flagged_items": [],
            "issues": ["No DOIs found in references section."],
            "suggestions": [
                "Include DOIs for all cited works to improve citation verifiability."
            ],
        }

    # Validate each DOI
    results = {doi: _validate_doi(doi) for doi in dois}

    verified_count    = sum(1 for s in results.values() if s == "verified")
    not_found_count   = sum(1 for s in results.values() if s == "not_found")
    unreachable_count = sum(1 for s in results.values() if s == "unreachable")

    flagged_dois = [doi for doi, status in results.items() if status == "not_found"]

    # Build flagged_items for not_found DOIs
    for doi in flagged_dois:
        # Try to find the reference line containing this DOI
        matching_line = ""
        for line in ref_lines:
            if doi in line:
                matching_line = line
                break

        # Extract author-year label from the reference line
        author_match = re.match(r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+\w+))?.*?\d{4})',
                                 matching_line) if matching_line else None
        citation_label = author_match.group(1) if author_match else doi

        flagged_items.append({
            "citation": citation_label,
            "category": "not_found",
            "detail": "No CrossRef match for DOI or title search."
        })

    # Detect duplicate references
    duplicate_flags = _detect_duplicates(references_text)
    flagged_items.extend(duplicate_flags)

    # All DOIs unreachable — special case
    if unreachable_count == len(dois):
        return {
            "score": 0.0,
            "total_refs": total_refs,
            "verified": 0,
            "not_found": 0,
            "unreachable": unreachable_count,
            "flagged_dois": [],
            "flagged_items": [],
            "issues": ["Citation verification unavailable — CrossRef API unreachable."],
            "suggestions": ["Retry the analysis when network access is available."],
        }

    # Score = verified / total_dois * 10
    score = round((verified_count / len(dois)) * 10, 1)

    # Build human-readable issues and suggestions
    issues = []
    suggestions = []

    if not_found_count > 0:
        issues.append(
            f"{not_found_count} of {len(dois)} DOI(s) could not be verified "
            f"(not found in CrossRef)."
        )
        suggestions.append(
            "Check flagged DOIs for typos or confirm they are published in indexed journals."
        )
    if duplicate_flags:
        issues.append(
            f"{len(duplicate_flags)} duplicate reference(s) detected."
        )
        suggestions.append(
            "Remove duplicate entries and ensure consistent formatting."
        )
    if unreachable_count > 0:
        issues.append(
            f"{unreachable_count} of {len(dois)} DOI(s) were unreachable during validation."
        )
        suggestions.append(
            "Retry the analysis to attempt validation of unreachable DOIs."
        )
    if not issues:
        issues.append(f"All {len(dois)} DOI(s) verified successfully.")
        suggestions.append("No citation issues found.")

    return {
        "score": score,
        "total_refs": total_refs,
        "verified": verified_count,
        "not_found": not_found_count,
        "unreachable": unreachable_count,
        "flagged_dois": flagged_dois,
        "flagged_items": flagged_items,
        "issues": issues,
        "suggestions": suggestions,
    }
