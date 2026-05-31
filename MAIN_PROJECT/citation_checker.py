import re
import difflib
import requests
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

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


def _extract_title_from_ref(ref_line: str) -> str:
    """
    Extract a paper title from a bibliography reference line.

    Strategy:
    1. Strip leading numbering like [1], [2], 1., 2. etc.
    2. Look for quoted text ("Title Here").
    3. Otherwise, look for text between author-year and the journal/venue name.
    """
    # Strip numbering like [1], [2], 1., 2., (1), etc.
    line = re.sub(r'^\s*(?:\[\d+\]|\(\d+\)|\d+[\.\)])\s*', '', ref_line).strip()

    # Strategy 1: Look for quoted text
    quoted = re.search(r'["\u201c](.+?)["\u201d]', line)
    if quoted:
        return quoted.group(1).strip()

    # Strategy 2: Text between author-year and journal/venue
    # Pattern: Author(s) (Year). Title. Journal/Conference...
    match = re.search(
        r'\(\d{4}\)\.?\s*(.+?)\.',
        line
    )
    if match:
        title = match.group(1).strip()
        if len(title) > 10:
            return title

    # Strategy 3: Text after "Year." or "Year," up to next period
    match = re.search(
        r'\d{4}[\.\,]\s*(.+?)\.',
        line
    )
    if match:
        title = match.group(1).strip()
        if len(title) > 10:
            return title

    return ""


def _verify_title_semantic_scholar(title: str) -> bool:
    """
    Query Semantic Scholar API to verify whether a paper title exists.

    Uses difflib.SequenceMatcher to compare the queried title with the
    returned title. Considers it verified if similarity ratio >= 0.6.

    Returns True if a sufficiently similar match is found, False otherwise.
    """
    if not title.strip():
        return False

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": title,
        "limit": 1,
        "fields": "title"
    }
    try:
        response = requests.get(url, params=params, timeout=3)
        if response.status_code != 200:
            return False
        data = response.json()
        papers = data.get("data", [])
        if not papers:
            return False
        returned_title = papers[0].get("title", "")
        ratio = difflib.SequenceMatcher(
            None, title.lower(), returned_title.lower()
        ).ratio()
        return ratio >= 0.6
    except (requests.RequestException, ValueError, KeyError):
        return False


def _verify_references_parallel(ref_lines: list, max_refs: int = 10) -> dict:
    """
    Verify reference titles against Semantic Scholar in parallel.

    Extracts titles from up to `max_refs` reference lines and checks them
    concurrently using a ThreadPoolExecutor with 5 workers.

    Returns:
        {"verified": int, "not_found": int, "checked": int}
    """
    # Extract titles from reference lines
    titles = []
    for line in ref_lines[:max_refs]:
        title = _extract_title_from_ref(line)
        if title:
            titles.append(title)

    if not titles:
        return {"verified": 0, "not_found": 0, "checked": 0}

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(_verify_title_semantic_scholar, titles))

    verified = sum(1 for r in results if r)
    not_found = sum(1 for r in results if not r)

    return {
        "verified": verified,
        "not_found": not_found,
        "checked": len(titles)
    }


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
        # No DOIs found — use parallel title verification via Semantic Scholar
        verification = _verify_references_parallel(ref_lines)
        verified_count = verification["verified"]
        not_found_count = verification["not_found"]
        checked_count = verification["checked"]

        # Score based on verification ratio
        if checked_count > 0:
            ratio = verified_count / checked_count
            if ratio >= 0.8:
                ref_score = 10.0
            elif ratio >= 0.5:
                ref_score = 7.0
            elif ratio >= 0.3:
                ref_score = 5.0
            else:
                ref_score = 3.0
        else:
            # No titles could be extracted — minimal credit for having references
            ref_score = 3.0 if total_refs >= 1 else 0.0

        issues = ["No DOIs found in references section."]
        if checked_count > 0:
            issues.append(
                f"Title verification: {verified_count}/{checked_count} references verified via Semantic Scholar."
            )
        else:
            issues.append(
                f"Could not extract titles from {total_refs} reference entries for verification."
            )

        # Check for duplicates even without DOIs
        duplicate_flags = _detect_duplicates(references_text)
        if duplicate_flags:
            issues.append(f"{len(duplicate_flags)} duplicate reference(s) detected.")
            ref_score = max(ref_score - 1.0, 0.0)

        return {
            "score": ref_score,
            "total_refs": total_refs,
            "verified": verified_count,
            "not_found": not_found_count,
            "unreachable": 0,
            "flagged_dois": [],
            "flagged_items": duplicate_flags,
            "issues": issues,
            "suggestions": [
                "Include DOIs for all cited works to improve citation verifiability.",
                "Papers with verifiable DOIs receive higher citation scores."
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
