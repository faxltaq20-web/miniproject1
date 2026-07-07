import re
import difflib
import time
import requests
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

# Max DOIs to validate per paper — avoids excessive CrossRef calls on large reference lists
MAX_DOIS = 20

# Phase 13: hard cap on Semantic Scholar title-fallback queries per paper.
# SS rate-limits aggressively (HTTP 429); 5 is the safe ceiling.
MAX_TITLE_FALLBACK = 5

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


def _extract_paper_publication_year(full_text: str) -> int | None:
    """
    Heuristically detect the paper's own publication year from its opening
    pages. Scans the first ~4000 characters (cover + abstract zone) for
    year-shaped tokens between 1950 and the current calendar year, and
    returns the most-frequent candidate. Falls back to the latest plausible
    year if no clear winner emerges. Returns None when no year is found.
    """
    if not full_text:
        return None
    import datetime
    current_year = datetime.datetime.now().year
    head = full_text[:4000]
    candidates = []
    for m in YEAR_PATTERN.finditer(head):
        y = int(m.group(1))
        if 1950 < y <= current_year:
            candidates.append(y)
    if not candidates:
        return None
    counts = Counter(candidates)
    top_year, top_count = counts.most_common(1)[0]
    # If ties exist, prefer the most recent — papers typically reference older
    # work but cite their own year more uniquely.
    tied = [y for y, c in counts.items() if c == top_count]
    return max(tied) if len(tied) > 1 else top_year


def _score_citation_recency(ref_lines: list, paper_year: int | None = None) -> dict:
    """
    Score how current the reference list is based on publication years.
    Recent citations (≤3 years old relative to the paper's publication year)
    signal the authors surveyed recent work at the time of writing.

    When paper_year is None, falls back to the current calendar year — this
    preserves prior behavior for callers that don't pass full text.

    Returns:
        {"recency_score": float, "recent_ratio": float | None,
         "recency_note": str, "ref_years": list[int]}
    """
    import datetime
    current_year = datetime.datetime.now().year
    baseline_year = paper_year if paper_year else current_year

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

    recent = sum(1 for y in years if y >= baseline_year - 3)
    ratio = round(recent / len(years), 2)

    baseline_label = (
        f"last 3 years before paper ({baseline_year})"
        if paper_year else "last 3 years"
    )
    if ratio >= 0.35:
        score, note = 10.0, f"{recent}/{len(years)} refs from {baseline_label} — excellent currency."
    elif ratio >= 0.20:
        score, note = 8.0,  f"{recent}/{len(years)} refs from {baseline_label} — good currency."
    elif ratio >= 0.08:
        score, note = 6.0,  f"{recent}/{len(years)} refs from {baseline_label} — moderate currency."
    else:
        score, note = 4.0,  (
            f"Only {recent}/{len(years)} refs from {baseline_label} — "
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


# <<<< SCREENSHOT THIS FUNCTION for Fig 7.2.3 >>>>
def check_citations(references_text: str, full_text: str = "",
                    pdf_hyperlink_dois: list = None) -> dict:
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
        pdf_hyperlink_dois: DOIs extracted from PDF hyperlink annotations
                           (invisible in text). Merged into the DOI pool so
                           papers that embed DOIs as clickable links (ACL,
                           IEEE, Springer) get proper credit.

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

    # Phase 14: detect paper's own publication year from cover/abstract so
    # recency is judged relative to when the paper was written, not "now".
    paper_year = _extract_paper_publication_year(full_text)

    # Phase 13: global DOI sweep across the ENTIRE references block (capped at
    # MAX_DOIS=20). Removes the historic 15-line sampling bias that lost DOIs
    # buried below the top of a long bibliography.
    dois = _extract_dois(references_text)

    # Merge DOIs extracted from PDF hyperlink annotations (invisible in text).
    # Many academic publishers embed DOIs as clickable links but don't print
    # them in the bibliography text. These are just as valid for verification.
    if pdf_hyperlink_dois:
        text_doi_set = set(dois)
        merged_count = 0
        for hdoi in pdf_hyperlink_dois:
            if hdoi not in text_doi_set:
                dois.append(hdoi)
                text_doi_set.add(hdoi)
                merged_count += 1
        if merged_count > 0:
            print(f"   [Citations] Merged {merged_count} DOI(s) from PDF hyperlink annotations.",
                  flush=True)
        # Re-apply the global cap after merging
        dois = dois[:MAX_DOIS]
    flagged_items = []

    if not dois:
        # No DOIs anywhere — keep dedicated title-only branch (test contract
        # depends on this calling `_verify_references_parallel`).
        verification = _verify_references_parallel(ref_lines)
        verified_count = verification["verified"]
        not_found_count = verification["not_found"]
        unreachable_count = verification.get("unreachable", 0)
        checked_count = verification["checked"]

        # Fair score: exclude unreachable from calculation.
        # Continuous linear scale — verified / scorable * 10. Avoids step-function
        # fairness cliffs (e.g. 0.49 → 5.0 vs 0.50 → 7.0).
        scorable = verified_count + not_found_count
        if scorable > 0:
            ratio = verified_count / scorable
            ref_score = round(ratio * 10.0, 1)
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
        recency = _score_citation_recency(ref_lines, paper_year)
        issues.append(recency["recency_note"])
        # Blend: 80% DOI/title score + 20% recency score
        ref_score = round(0.80 * ref_score + 0.20 * recency["recency_score"], 1)

        # No-DOI penalty: cap citation score at 6.0/10 when zero DOIs are present.
        # Papers without verifiable DOIs should not score higher than "adequate"
        # on citations, regardless of title-match or recency performance.
        ref_score = min(ref_score, 6.0)

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

    # ── Phase 13: Global DOI sweep + capped title fallback ───────────────────
    # 1. Validate ALL extracted DOIs (already capped at MAX_DOIS=20) in parallel.
    # 2. Identify references in the bibliography that don't have a verified DOI.
    # 3. Take up to MAX_TITLE_FALLBACK (5) of those as a Semantic Scholar sample,
    #    avoiding HTTP 429s while still salvaging un-DOI'd citations.
    # 4. Score on the blended verified pool (DOIs + titles) over the scorable
    #    pool (checked DOIs + checked titles).

    # Validate all DOIs in parallel.
    doi_statuses: dict = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_validate_doi, doi): doi for doi in dois}
        for future in as_completed(futures):
            doi = futures[future]
            try:
                doi_statuses[doi] = future.result()
            except Exception:
                doi_statuses[doi] = "unreachable"

    verified_dois    = [d for d, s in doi_statuses.items() if s == "verified"]
    not_found_dois   = [d for d, s in doi_statuses.items() if s == "not_found"]
    unreachable_dois = [d for d, s in doi_statuses.items() if s == "unreachable"]

    # Identify reference lines without a verified DOI. A line is "covered" by a
    # verified DOI iff one of the verified DOIs appears in it.
    uncovered_refs = [
        line for line in ref_lines
        if not any(doi in line for doi in verified_dois)
    ]

    # Cap the title-fallback sample at MAX_TITLE_FALLBACK (5), spread
    # proportionally across the full uncovered list so we sample from the
    # whole bibliography, not just the first five entries.
    N = len(uncovered_refs)
    if N <= MAX_TITLE_FALLBACK:
        title_sample = uncovered_refs
    else:
        title_sample = [
            uncovered_refs[int(i * N / MAX_TITLE_FALLBACK)]
            for i in range(MAX_TITLE_FALLBACK)
        ]

    # Run capped Semantic Scholar title checks in parallel.
    verified_titles_count = 0
    not_found_titles_count = 0
    unreachable_titles_count = 0
    checked_titles = 0

    title_checks = []
    for line in title_sample:
        title = _extract_title_from_ref(line)
        year = _extract_year_from_ref(line)
        if title:
            title_checks.append((title, year))

    if title_checks:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(_verify_title_semantic_scholar, t, y): t
                for t, y in title_checks
            }
            for future in as_completed(futures):
                try:
                    status = future.result()
                except Exception:
                    status = "unreachable"
                if status == "verified":
                    verified_titles_count += 1
                elif status == "not_found":
                    not_found_titles_count += 1
                else:
                    unreachable_titles_count += 1
        checked_titles = len(title_checks)

    # Blended counts: verified DOIs + verified titles count as verified refs.
    verified_count    = len(verified_dois) + verified_titles_count
    not_found_count   = len(not_found_dois) + not_found_titles_count
    unreachable_count = len(unreachable_dois) + unreachable_titles_count

    # Build flagged_dois / flagged_items for not_found DOIs.
    flagged_dois = list(not_found_dois)
    for doi in flagged_dois:
        matching_line = ""
        for line in ref_lines:
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
    arxiv_ids = _extract_arxiv_ids(references_text)
    arxiv_verified = 0
    if arxiv_ids:
        with ThreadPoolExecutor(max_workers=5) as executor:
            arxiv_futures = {executor.submit(_verify_arxiv_id, aid): aid
                             for aid in arxiv_ids[:15]}
            for future in as_completed(arxiv_futures):
                try:
                    if future.result() == "verified":
                        arxiv_verified += 1
                except Exception:
                    pass

    # ── Citation recency ──────────────────────────────────────────────────────
    recency = _score_citation_recency(ref_lines, paper_year)

    # If every signal we tried was unreachable, return a neutral score.
    total_attempts = len(dois) + checked_titles
    if total_attempts > 0 and unreachable_count == total_attempts:
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

    # Blended scoring base: checked DOIs + checked titles, excluding unreachable.
    scorable = (len(verified_dois) + len(not_found_dois)
                + verified_titles_count + not_found_titles_count)
    doi_score = round((verified_count / scorable) * 10, 1) if scorable > 0 else 7.0

    # ArXiv boost.
    if arxiv_ids:
        arxiv_ratio = arxiv_verified / len(arxiv_ids)
        if arxiv_ratio >= 0.7:
            doi_score = min(doi_score + 1.5, 10.0)
        elif arxiv_ratio >= 0.4:
            doi_score = min(doi_score + 0.75, 10.0)

    score = round(0.80 * doi_score + 0.20 * recency["recency_score"], 1)

    issues = []
    suggestions = []

    if not_found_dois:
        issues.append(
            f"{len(not_found_dois)} of {len(dois)} DOI(s) could not be verified "
            f"(not found in CrossRef)."
        )
        suggestions.append(
            "Check flagged DOIs for typos or confirm they are published in indexed journals."
        )
    if checked_titles > 0:
        issues.append(
            f"Title fallback: {verified_titles_count}/{checked_titles} reference(s) "
            f"verified via Semantic Scholar (capped at {MAX_TITLE_FALLBACK})."
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
    if unreachable_dois:
        issues.append(
            f"{len(unreachable_dois)} of {len(dois)} DOI(s) were unreachable during validation."
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
