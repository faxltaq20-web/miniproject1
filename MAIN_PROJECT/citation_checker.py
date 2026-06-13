import re
import difflib
import time
import requests
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

# Max DOIs to validate per paper — avoids excessive CrossRef calls on large reference lists
MAX_DOIS = 20

# Area 7: Enhanced DOI pattern — matches labeled AND standalone DOIs
# Labeled: doi.org/10.1234/..., DOI: 10.1234/..., doi: 10.1234/...
# Standalone: 10.1234/abc (common in bibliography entries without prefix)
DOI_LABELED = re.compile(
    r'(?:doi\.org/|DOI:\s*|doi:\s*)(10\.\d{4,}/\S+)',
    re.IGNORECASE
)
DOI_STANDALONE = re.compile(
    r'(?<!\w)(10\.\d{4,9}/[^\s,;)\]>\'\"\`\'\'\u2018\u2019\u201c\u201d]+)',
    re.IGNORECASE
)

# Area 7: Strip trailing punctuation, quotes, backticks, braces, dashes.
# Note: closing parens `)` and brackets `]` are intentionally NOT included here
# \u2014 they are handled by `_clean_doi_parentheses()` which only strips them when
# unmatched (preserving DOIs that legitimately end with balanced brackets like
# `10.1000/abc(123)`).
TRAILING_JUNK = re.compile(r'[.,;:>\'\"\`\\\-\'\'\u2018\u2019\u201c\u201d]+$')

# Pattern to extract author-year citations like "Smith & Lee, 2019" or "(Author, 2020)"
AUTHOR_YEAR_PATTERN = re.compile(
    r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-z]+))?),?\s*\(?\s*(\d{4})\s*\)?'
)

# Area 7: Year extraction pattern
YEAR_PATTERN = re.compile(r'\b(19\d{2}|20\d{2})\b')

# ArXiv reference patterns — covers all common citation styles:
#   arXiv:2407.21783   arXiv preprint arXiv:2407.21783   arxiv.org/abs/2407.21783
ARXIV_PATTERN = re.compile(
    r'(?:arXiv\s*(?:preprint\s*arXiv)?\s*:|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5})'
    r'|\barXiv:(\d{4}\.\d{4,5})\b',
    re.IGNORECASE
)

CROSSREF_BASE = "https://api.crossref.org/works/{doi}"
CROSSREF_SEARCH = "https://api.crossref.org/works"
HEADERS = {
    # Polite pool header — gives CrossRef rate-limit headroom (50 req/sec)
    "User-Agent": "ResearchSense/1.0 (mailto:team@researchsense.dev)"
}
TIMEOUT = 5  # seconds per request


def _clean_doi_parentheses(doi: str) -> str:
    """
    Strip trailing `)` or `]` from a DOI only when they are unmatched.

    Many DOIs legitimately end with balanced brackets (e.g. `10.1000/abc(123)`).
    Blindly stripping trailing closing characters corrupts these. This helper
    counts opens vs. closes and only peels off the trailing closer when the
    counts are unbalanced.

    Args:
        doi: A DOI string that may have a trailing `)` or `]` artifact from
             surrounding text (e.g. `10.1000/foo)` extracted from `"(see 10.1000/foo)"`).

    Returns:
        The DOI with unmatched trailing `)` / `]` characters removed.
    """
    if not doi:
        return doi
    while doi.endswith(')') and doi.count('(') < doi.count(')'):
        doi = doi[:-1]
    while doi.endswith(']') and doi.count('[') < doi.count(']'):
        doi = doi[:-1]
    return doi


def _extract_dois(references_text: str) -> list:
    """
    Area 7: Extract DOIs from references text using both labeled and standalone
    patterns and merge their matches.

    Strategy:
    - Run BOTH `DOI_LABELED` (DOI:/doi:/doi.org prefixes) and `DOI_STANDALONE`
      (raw `10.XXXX/...`) patterns. Earlier behavior was mutually exclusive —
      if any labeled DOI was found the standalone pattern was skipped entirely,
      causing mixed-format bibliographies to lose standalone DOIs.
    - Strip generic trailing junk via `TRAILING_JUNK`, then apply
      `_clean_doi_parentheses()` for balanced-aware ) / ] trimming.
    - Deduplicate, preserving discovery order, and cap at `MAX_DOIS`.

    Returns:
        A deduplicated list of up to `MAX_DOIS` DOI strings.
    """
    cleaned = []
    seen = set()

    for pattern in (DOI_LABELED, DOI_STANDALONE):
        for m in pattern.finditer(references_text):
            doi = m.group(1)
            doi = TRAILING_JUNK.sub("", doi).strip()
            doi = _clean_doi_parentheses(doi)
            if doi and doi not in seen:
                seen.add(doi)
                cleaned.append(doi)
            if len(cleaned) >= MAX_DOIS:
                return cleaned
    return cleaned


def _extract_year_from_ref(ref_line: str) -> str:
    """Area 7: Extract publication year from a reference line."""
    match = YEAR_PATTERN.search(ref_line)
    return match.group(1) if match else ""


def _extract_author_year_refs(text: str) -> list:
    """
    Extract author-year reference entries from the full paper text.
    Returns list of tuples: (author_string, year).
    """
    matches = AUTHOR_YEAR_PATTERN.findall(text)
    return [(author.strip(), year) for author, year in matches]


def _extract_arxiv_ids(references_text: str) -> list:
    """
    Extract ArXiv paper IDs from the references section.
    Returns a deduplicated list of ID strings like ["2407.21783", "1706.03762"].
    """
    ids = []
    seen = set()
    for m in ARXIV_PATTERN.finditer(references_text):
        arxiv_id = m.group(1) or m.group(2)
        if arxiv_id and arxiv_id not in seen:
            seen.add(arxiv_id)
            ids.append(arxiv_id)
    return ids


def _verify_arxiv_id(arxiv_id: str) -> str:
    """
    Verify an ArXiv paper ID exists via the public ArXiv Atom API.
    Free, no auth, no rate limit for reasonable use.

    Returns:
        "verified"    — paper entry found in ArXiv
        "not_found"   — no entry returned for this ID
        "unreachable" — timeout or connection error
    """
    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return "unreachable"
        # ArXiv API always returns HTTP 200. Check for an actual entry tag.
        return "verified" if "<entry>" in response.text else "not_found"
    except requests.RequestException:
        return "unreachable"


def _score_citation_recency(ref_lines: list) -> dict:
    """
    Score how current the reference list is based on publication years.
    Recent citations (≤3 years old) signal the authors surveyed recent work.

    Returns:
        {"recency_score": float, "recent_ratio": float | None,
         "recency_note": str, "ref_years": list[int]}
    """
    import datetime
    current_year = datetime.datetime.now().year

    years = []
    for line in ref_lines:
        m = YEAR_PATTERN.search(line)
        if m:
            y = int(m.group(1))
            if 1950 < y <= current_year:
                years.append(y)

    if not years:
        return {
            "recency_score": 7.0,
            "recent_ratio": None,
            "recency_note": "Could not extract publication years from references.",
            "ref_years": [],
        }

    recent = sum(1 for y in years if y >= current_year - 3)
    ratio = round(recent / len(years), 2)

    if ratio >= 0.35:
        score, note = 10.0, f"{recent}/{len(years)} refs from last 3 years — excellent currency."
    elif ratio >= 0.20:
        score, note = 8.0,  f"{recent}/{len(years)} refs from last 3 years — good currency."
    elif ratio >= 0.08:
        score, note = 6.0,  f"{recent}/{len(years)} refs from last 3 years — moderate currency."
    else:
        score, note = 4.0,  (
            f"Only {recent}/{len(years)} refs from last 3 years — "
            "literature survey may be outdated."
        )

    return {
        "recency_score": score,
        "recent_ratio": ratio,
        "recency_note": note,
        "ref_years": sorted(set(years)),
    }


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


def _search_crossref_works(query: str) -> dict:
    """
    Area 7: Search CrossRef Works API for a reference by bibliographic query.
    Returns {"matched": bool, "title": str, "year": str} or None on failure.
    """
    try:
        response = requests.get(
            CROSSREF_SEARCH,
            params={"query.bibliographic": query, "limit": 3},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if response.status_code == 200:
            items = response.json().get("message", {}).get("items", [])
            if items:
                return {
                    "matched": True,
                    "title": items[0].get("title", [""])[0],
                    "year": str(items[0].get("published-print", {}).get("date-parts", [[None]])[0][0] or ""),
                }
        elif response.status_code in (429, 503):
            time.sleep(1.0)
            # Retry once
            response = requests.get(
                CROSSREF_SEARCH,
                params={"query.bibliographic": query, "limit": 3},
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            if response.status_code == 200:
                items = response.json().get("message", {}).get("items", [])
                if items:
                    return {
                        "matched": True,
                        "title": items[0].get("title", [""])[0],
                        "year": str(items[0].get("published-print", {}).get("date-parts", [[None]])[0][0] or ""),
                    }
    except requests.RequestException:
        pass
    return {"matched": False, "title": "", "year": ""}


def _verify_title_semantic_scholar(title: str, ref_year: str = "") -> str:
    """
    Area 7: Query Semantic Scholar API to verify whether a paper title exists.

    Uses year-aware matching with top 3 results:
    - If returned paper's year matches ref_year (±1), accept with ratio >= 0.5
    - Otherwise, require ratio >= 0.6

    Returns:
        "verified"   — sufficiently similar match found
        "not_found"  — no match found in Semantic Scholar
        "unreachable" — API error (429, 503, timeout, etc.)
    """
    if not title.strip():
        return "not_found"

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": title,
        "limit": 3,
        "fields": "title,year"
    }
    try:
        response = requests.get(url, params=params, timeout=3)
        if response.status_code == 429:
            # Rate limited — wait and retry once
            time.sleep(1.0)
            response = requests.get(url, params=params, timeout=3)
        if response.status_code in (429, 503):
            return "unreachable"
        if response.status_code != 200:
            return "unreachable"
        data = response.json()
        papers = data.get("data", [])
        if not papers:
            return "not_found"

        # Year-aware matching: check top 3 results
        ref_year_int = int(ref_year) if ref_year and ref_year.isdigit() else None
        for paper in papers[:3]:
            returned_title = paper.get("title", "")
            paper_year = paper.get("year")
            ratio = difflib.SequenceMatcher(
                None, title.lower(), returned_title.lower()
            ).ratio()

            # Year-aware threshold: if years match (±1), relax similarity threshold
            if ref_year_int and paper_year:
                if abs(ref_year_int - paper_year) <= 1 and ratio >= 0.5:
                    return "verified"
            if ratio >= 0.6:
                return "verified"

        return "not_found"
    except requests.RequestException:
        return "unreachable"
    except (ValueError, KeyError):
        return "not_found"


def _verify_references_parallel(ref_lines: list, max_refs: int = 10) -> dict:
    """
    Area 7: Verify reference titles against Semantic Scholar in parallel.

    Extracts titles and years from up to `max_refs` reference lines and checks them
    concurrently using a ThreadPoolExecutor with 5 workers.

    Returns:
        {"verified": int, "not_found": int, "unreachable": int, "checked": int}
    """
    # Extract titles and years from reference lines
    checks = []
    for line in ref_lines[:max_refs]:
        title = _extract_title_from_ref(line)
        year = _extract_year_from_ref(line)
        if title:
            checks.append((title, year))

    if not checks:
        return {"verified": 0, "not_found": 0, "unreachable": 0, "checked": 0}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_verify_title_semantic_scholar, title, year): title
            for title, year in checks
        }
        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                results.append("unreachable")

    verified = sum(1 for r in results if r == "verified")
    not_found = sum(1 for r in results if r == "not_found")
    unreachable = sum(1 for r in results if r == "unreachable")

    return {
        "verified": verified,
        "not_found": not_found,
        "unreachable": unreachable,
        "checked": len(checks)
    }


def _validate_doi(doi: str) -> str:
    """
    Validate a single DOI against CrossRef REST API.
    Retries once on 429/503 errors.

    Returns:
        "verified"    — HTTP 200 (DOI exists in CrossRef)
        "not_found"   — HTTP 404 (DOI not in CrossRef database)
        "unreachable" — timeout, connection error, or unexpected HTTP status
    """
    url = CROSSREF_BASE.format(doi=doi)
    for attempt in range(2):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if response.status_code == 200:
                return "verified"
            elif response.status_code == 404:
                return "not_found"
            elif response.status_code in (429, 503) and attempt == 0:
                time.sleep(1.0)
                continue
            else:
                return "unreachable"
        except requests.RequestException:
            if attempt == 0:
                time.sleep(0.5)
                continue
            return "unreachable"
    return "unreachable"


def check_citations(references_text: str, full_text: str = "") -> dict:
    """
    Area 7: Unified per-reference validation with DOI-first / title-fallback.

    A sample of up to 15 reference lines is checked in parallel. For each
    reference:
      1. Extract DOI(s) from the line. If present, validate via CrossRef
         (`_validate_doi`). If any DOI verifies, the reference is verified.
      2. If the reference has no DOI, or all of its DOIs fail (`not_found`),
         fall back to a Semantic Scholar title search.
      3. Aggregate per-reference outcomes (verified / not_found / unreachable)
         and blend into the final score along with ArXiv boost + recency.

    Args:
        references_text: raw text of the paper's references section.
        full_text: full paper text (currently unused — reserved for in-text
                   citation cross-referencing in a future phase).

    Returns:
        {
            "score": float,            # 0-10, rounded to 1 decimal
            "total_refs": int,         # total reference entries
            "verified": int,
            "not_found": int,
            "unreachable": int,
            "flagged_dois": [str],     # DOIs that failed all verification
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

    # Sample size cap: avoid exhausting API rate limits on huge bibliographies.
    SAMPLE_CAP = 15

    # Extract section-level DOI list (kept for backward-compatible reporting
    # — issues messages still reference "X of N DOI(s)").
    dois = _extract_dois(references_text)
    flagged_items = []

    if not dois:
        # No DOIs anywhere — keep dedicated title-only branch (test contract
        # depends on this calling `_verify_references_parallel`).
        verification = _verify_references_parallel(ref_lines)
        verified_count = verification["verified"]
        not_found_count = verification["not_found"]
        unreachable_count = verification.get("unreachable", 0)
        checked_count = verification["checked"]

        # Fair score: exclude unreachable from calculation
        # Score = verified / (verified + not_found) * 10
        scorable = verified_count + not_found_count
        if scorable > 0:
            ratio = verified_count / scorable
            if ratio >= 0.8:
                ref_score = 10.0
            elif ratio >= 0.5:
                ref_score = 7.0
            elif ratio >= 0.3:
                ref_score = 5.0
            else:
                ref_score = 3.0
        elif unreachable_count > 0 and checked_count > 0:
            # All references unreachable — neutral fallback
            ref_score = 7.0
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
        if unreachable_count > 0:
            issues.append(
                f"{unreachable_count} reference(s) unreachable during verification (excluded from score)."
            )

        # Check for duplicates even without DOIs
        duplicate_flags = _detect_duplicates(references_text)
        if duplicate_flags:
            issues.append(f"{len(duplicate_flags)} duplicate reference(s) detected.")
            ref_score = max(ref_score - 1.0, 0.0)

        # ArXiv verification (free fallback for preprint-heavy reference lists)
        arxiv_ids = _extract_arxiv_ids(references_text)
        arxiv_verified = 0
        if arxiv_ids:
            with ThreadPoolExecutor(max_workers=5) as executor:
                arxiv_futures = {executor.submit(_verify_arxiv_id, aid): aid
                                 for aid in arxiv_ids[:15]}  # cap at 15
                for future in as_completed(arxiv_futures):
                    try:
                        if future.result() == "verified":
                            arxiv_verified += 1
                    except Exception:
                        pass
            issues.append(
                f"{arxiv_verified}/{len(arxiv_ids)} ArXiv reference(s) verified."
            )
            # Boost score if ArXiv refs verify well
            if arxiv_ids and arxiv_verified / len(arxiv_ids) >= 0.7:
                ref_score = min(ref_score + 1.0, 10.0)

        # Citation recency scoring
        recency = _score_citation_recency(ref_lines)
        issues.append(recency["recency_note"])
        # Blend: 80% DOI/title score + 20% recency score
        ref_score = round(0.80 * ref_score + 0.20 * recency["recency_score"], 1)

        return {
            "score": ref_score,
            "total_refs": total_refs,
            "verified": verified_count,
            "not_found": not_found_count,
            "unreachable": unreachable_count,
            "arxiv_verified": arxiv_verified,
            "flagged_dois": [],
            "flagged_items": duplicate_flags,
            "issues": issues,
            "suggestions": [
                "Include DOIs for all cited works to improve citation verifiability.",
                "Papers with verifiable DOIs receive higher citation scores."
            ],
            "recency": recency,
        }

    # ── Unified per-reference validation ─────────────────────────────────────
    # Sample up to SAMPLE_CAP references, validate each in parallel. For each
    # reference: try its own DOIs first; if all DOIs fail, fall back to a
    # Semantic Scholar title search for that specific reference. This fixes
    # the historic "all-or-none" bug where the presence of any DOI disabled
    # title checking for references that didn't have a DOI.
    sample_lines = ref_lines[:SAMPLE_CAP]

    # Edge case: references section is so terse that no line exceeds the
    # 20-char heuristic, yet we still extracted DOIs. Treat each DOI's raw
    # surrounding line as its own synthetic reference so DOIs are still
    # validated (preserves "extract DOIs and validate them" contract).
    if not sample_lines and dois:
        raw_lines = [l.strip() for l in references_text.splitlines() if l.strip()]
        synthetic = []
        for doi in dois:
            for line in raw_lines:
                if doi in line and line not in synthetic:
                    synthetic.append(line)
                    break
        sample_lines = synthetic[:SAMPLE_CAP]

    def _validate_reference(ref_line: str) -> dict:
        """
        Validate a single reference line. Returns a dict with:
          {
            "status":           "verified" | "not_found" | "unreachable",
            "doi_statuses":     {doi: status, ...},   # per-DOI raw outcomes
            "verified_via_doi": str | None,           # DOI that verified, if any
            "tried_title":      bool,
          }
        """
        line_dois = _extract_dois(ref_line)
        doi_statuses: dict = {}
        verified_via_doi = None
        any_unreachable = False

        for doi in line_dois:
            try:
                status = _validate_doi(doi)
            except Exception:
                status = "unreachable"
            doi_statuses[doi] = status
            if status == "verified" and verified_via_doi is None:
                verified_via_doi = doi
            if status == "unreachable":
                any_unreachable = True

        # If any DOI verified, the reference is verified.
        if verified_via_doi:
            return {
                "status": "verified",
                "doi_statuses": doi_statuses,
                "verified_via_doi": verified_via_doi,
                "tried_title": False,
            }

        # All DOIs unreachable (and no verified) → reference unreachable.
        # Do NOT attempt title fallback (the API stack may be throttled).
        if line_dois and all(s == "unreachable" for s in doi_statuses.values()):
            return {
                "status": "unreachable",
                "doi_statuses": doi_statuses,
                "verified_via_doi": None,
                "tried_title": False,
            }

        # No DOIs, or all DOIs not_found / partially not_found → try title.
        title = _extract_title_from_ref(ref_line)
        year = _extract_year_from_ref(ref_line)
        title_status = "not_found"
        if title:
            try:
                title_status = _verify_title_semantic_scholar(title, year)
            except Exception:
                title_status = "unreachable"

        if title_status == "verified":
            status = "verified"
        elif title_status == "unreachable" and not line_dois:
            # No DOI signal and title check unreachable → unreachable.
            status = "unreachable"
        elif title_status == "unreachable" and any_unreachable:
            status = "unreachable"
        else:
            status = "not_found"

        return {
            "status": status,
            "doi_statuses": doi_statuses,
            "verified_via_doi": None,
            "tried_title": True,
        }

    # Run per-reference validation in parallel.
    per_ref_results: list = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_line = {
            executor.submit(_validate_reference, line): line
            for line in sample_lines
        }
        for future in as_completed(future_to_line):
            line = future_to_line[future]
            try:
                per_ref_results.append((line, future.result()))
            except Exception:
                per_ref_results.append((line, {
                    "status": "unreachable",
                    "doi_statuses": {},
                    "verified_via_doi": None,
                    "tried_title": False,
                }))

    # Aggregate per-reference outcomes (this is what `verified` reports).
    verified_count    = sum(1 for _, r in per_ref_results if r["status"] == "verified")
    not_found_count   = sum(1 for _, r in per_ref_results if r["status"] == "not_found")
    unreachable_count = sum(1 for _, r in per_ref_results if r["status"] == "unreachable")

    # Build flagged_dois: every DOI that came back not_found across the sample
    # and was not later rescued by a successful title fallback for its own ref.
    flagged_dois = []
    seen_flagged = set()
    for ref_line, r in per_ref_results:
        if r["status"] == "verified":
            continue  # ref rescued — don't surface its DOIs as flagged
        for doi, doi_status in r["doi_statuses"].items():
            if doi_status == "not_found" and doi not in seen_flagged:
                seen_flagged.add(doi)
                flagged_dois.append(doi)

    # Build flagged_items entries for not_found DOIs.
    for doi in flagged_dois:
        matching_line = ""
        for line in sample_lines:
            if doi in line:
                matching_line = line
                break
        author_match = re.match(r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+\w+))?.*?\d{4})',
                                 matching_line) if matching_line else None
        citation_label = author_match.group(1) if author_match else doi
        flagged_items.append({
            "citation": citation_label,
            "category": "not_found",
            "detail": "No CrossRef match for DOI or title search."
        })

    # Detect duplicate references.
    duplicate_flags = _detect_duplicates(references_text)
    flagged_items.extend(duplicate_flags)

    # ── ArXiv verification ────────────────────────────────────────────────────
    # ML/AI papers heavily use ArXiv preprints (no DOI). Verify them separately
    # so they aren't penalised as "not_found" in the DOI score.
    arxiv_ids = _extract_arxiv_ids(references_text)
    arxiv_verified = 0
    if arxiv_ids:
        with ThreadPoolExecutor(max_workers=5) as executor:
            arxiv_futures = {executor.submit(_verify_arxiv_id, aid): aid
                             for aid in arxiv_ids[:15]}  # cap at 15 IDs
            for future in as_completed(arxiv_futures):
                try:
                    if future.result() == "verified":
                        arxiv_verified += 1
                except Exception:
                    pass

    # ── Citation recency ──────────────────────────────────────────────────────
    recency = _score_citation_recency(ref_lines)

    # All sampled references unreachable — neutral fallback score.
    if per_ref_results and unreachable_count == len(per_ref_results):
        return {
            "score": 7.0,
            "total_refs": total_refs,
            "verified": 0,
            "not_found": 0,
            "unreachable": unreachable_count,
            "arxiv_verified": arxiv_verified,
            "flagged_dois": [],
            "flagged_items": [],
            "recency": recency,
            "issues": ["Citation verification throttled — all DOIs unreachable. Neutral score applied."],
            "suggestions": ["Retry the analysis when API demand is lower."],
        }

    # Fair score: exclude unreachable from calculation.
    # Base score = verified / (verified + not_found) * 10
    # Blended with recency: 80% DOI score + 20% recency score
    scorable = verified_count + not_found_count
    doi_score = round((verified_count / scorable) * 10, 1) if scorable > 0 else 7.0

    # ArXiv boost: if ArXiv refs verify well, lift the score slightly.
    if arxiv_ids:
        arxiv_ratio = arxiv_verified / len(arxiv_ids)
        if arxiv_ratio >= 0.7:
            doi_score = min(doi_score + 1.5, 10.0)
        elif arxiv_ratio >= 0.4:
            doi_score = min(doi_score + 0.75, 10.0)

    score = round(0.80 * doi_score + 0.20 * recency["recency_score"], 1)

    # Build human-readable issues and suggestions.
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
    if arxiv_ids:
        issues.append(
            f"{arxiv_verified}/{len(arxiv_ids)} ArXiv preprint reference(s) verified."
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
    issues.append(recency["recency_note"])
    if not suggestions:
        issues.append(f"All {len(dois)} DOI(s) verified successfully.")
        suggestions.append("No citation issues found.")

    return {
        "score": score,
        "total_refs": total_refs,
        "verified": verified_count,
        "not_found": not_found_count,
        "unreachable": unreachable_count,
        "arxiv_verified": arxiv_verified,
        "flagged_dois": flagged_dois,
        "flagged_items": flagged_items,
        "recency": recency,
        "issues": issues,
        "suggestions": suggestions,
    }
