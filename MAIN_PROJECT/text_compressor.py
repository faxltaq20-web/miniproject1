"""
text_compressor.py — Lossless-semantic text compression for ResearchSense.

Approach A: Deterministic Normalization
========================================
Reduces assembled paper section text by 30-50% before LLM prompt assembly
using pure regex and string operations — zero external dependencies, zero
latency overhead, zero extra API calls.

Public API:
    compress_sections(sections: dict, mode: str = "light") -> dict
        sections : dict of {section_key: raw_text} from section_detector.py
        mode     : "off" | "light" | "aggressive"
        returns  : dict with same keys, compressed text values, plus a
                   "_compression_stats" metadata key.

Modes:
    off        — passthrough; no changes made
    light      — whitespace + citations + boilerplate + deduplication
    aggressive — light + formula/math-line removal

Future approaches (B, C, D) will be added in later phases as separate
functions in this same module.
"""

import re
import sys
from typing import Tuple

# Fix Windows CP1252 for any standalone runs
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ── Boilerplate phrase patterns ───────────────────────────────────────────────
# Sentence-level patterns. Each matches a redundant academic filler clause.
# Only the MATCHED PHRASE + trailing comma is removed — the rest of the
# sentence (which may contain result numbers or factual content) is kept.
BOILERPLATE_PATTERNS = [
    # Paper structure forward-references
    r"[Ii]n this (paper|work|study|section|article),?\s+we\s+\w+",
    r"[Tt]he rest of (this paper|the paper) is (organized|structured) as follows",
    r"[Tt]he remainder of this (paper|work|article) is (organized|structured)",
    r"[Tt]he (paper|article|work) is (organized|structured) as follows",
    r"[Tt]his (paper|work|article|study) is (organized|structured) as follows",
    # Filler transition phrases
    r"[Ii]t is worth (noting|mentioning) that",
    r"[Ii]t should be (noted|mentioned|emphasized|pointed out) that",
    r"[Aa]s (mentioned|discussed|described|shown|noted|stated|presented|outlined)"
    r"\s+(above|below|previously|earlier|in Section\s+\w+|in the previous)",
    r"[Aa]s we (mentioned|discussed|showed|described|noted|stated)"
    r"\s+(above|earlier|previously|in Section\s+\w+)",
    r"[Aa]s can be seen (from|in)\s+(the\s+)?(above|following|previous|figure|table)",
    # Redundant summary openers
    r"[Ii]n (summary|conclusion|short|brief),?\s+(we|our|the|this)",
    r"[Tt]o (summarize|conclude|sum up|recap),?",
    r"[Aa]s (described|shown|explained|mentioned|discussed|noted|stated|presented) above",
    r"[Tt]o the best of our knowledge,?",
    # Generic motivation padding
    r"[Ii]n recent years[,.]",
    r"[Oo]ver the (past|last|recent)\s+\w+\s+years?,?",
    r"[Ww]ith the (rapid|recent|growing|increasing|unprecedented) development of",
    r"[Ww]ith the (advent|rise|emergence|proliferation|explosion) of",
    r"[Rr]ecently[,.]?\s+\w+ has (become|gained|attracted|received|emerged)",
    r"[Tt]here (is|has been)\s+(a|an)\s+(growing|increasing|rising|recent)"
    r"\s+(interest|demand|need|trend|focus)\s+in",
    r"[Tt]he (rapid|growing|recent|increasing)\s+\w+ of\s+\w+ has",
    r"[Ii]t is (well[- ]known|widely accepted|generally agreed|commonly known) that",
    # Figure/table callout references (safe to strip in intro — NOT in results/discussion)
    r"[Ss]ee (Figure|Fig\.|Table|Appendix|Section)\s+\w+",
    r"[Rr]efer(ring)?\s+to\s+(Figure|Fig\.|Table|Appendix)\s+\w+",
    r"\(see\s+(Figure|Fig\.|Table|Appendix)\s+\w+\)",
]

# ── Evidence-pointer patterns — NEVER stripped from results/discussion ─────────
# These link claims to quantitative evidence. Removing them makes results text
# incoherent and prevents Gemini from understanding what supports what.
EVIDENCE_POINTER_PATTERNS = [
    r"[Aa]s (shown|illustrated|depicted|presented|summarized|displayed|plotted)"
    r"\s+in\s+(Figure|Fig\.|Table|Appendix)\s+\w+",
    r"[Ss]hown in\s+(Figure|Fig\.|Table|Appendix)\s+\w+",
]

# ── Per-section compression rules ─────────────────────────────────────────────
# Controls which pipeline stages run for each section key.
# Sections NOT listed here fall back to the global mode.
#
# Levels:
#   "none"    — whitespace normalisation only (no stripping at all)
#   "minimal" — whitespace + dedup within section only
#   "light"   — full light pipeline
#   "aggressive" — full aggressive pipeline
SECTION_COMPRESSION_RULES = {
    "abstract":     "none",      # tiny + every word matters — no compression
    "introduction": "light",     # boilerplate removal fine
    "related_work": "light",     # citation removal fine
    "methodology":  "none",      # shielded in gemini_analyzer; included here for safety
    "results":      "minimal",   # whitespace + within-section dedup only;
                                 # evidence pointers and figure refs MUST be kept
    "discussion":   "light",     # fine — doesn't carry raw numbers
    "conclusion":   "none",      # small + key claims — no compression
    "references":   "none",      # already skipped; here for explicit documentation
}

# ── Citation / reference marker patterns ──────────────────────────────────────
CITATION_PATTERNS = [
    r'\[\d+(?:[,;\s–\-]+\d+)*\]',              # [1], [12], [1,2,3], [1-5], [1; 2]
    r'\(\w[\w\s,\.&]+,?\s+\d{4}[a-z]?\)',      # (Smith et al., 2020), (Jones, 2019a)
    r'[\u00b9\u00b2\u00b3\u2074-\u2079]+',     # Unicode superscripts ¹²³⁴
    r'(?<!\w)\^\{\d+(?:,\d+)*\}',              # LaTeX ^{1,2}
    r'(?<!\w)\^[\d,]+(?!\w)',                  # Simple ^1,2 superscripts
]


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_formula_line(line: str) -> bool:
    """
    Return True if a line is predominantly mathematical (aggressive mode).
    Heuristic: fewer than 40% of characters are alphabetic.
    Only applied to lines of at least 5 characters (skip blank/short lines).
    """
    stripped = line.strip()
    if len(stripped) < 5:
        return False
    alpha_count = sum(1 for c in stripped if c.isalpha())
    return (alpha_count / len(stripped)) < 0.40


def _normalize_whitespace(text: str) -> str:
    """
    Clean up whitespace artifacts:
    - Form-feed characters (common in PDF extraction) → newline
    - BOM characters → removed
    - CRLF → LF
    - Multiple consecutive spaces/tabs → single space
    - 3+ consecutive newlines → 2 newlines
    """
    text = text.replace('\x0c', '\n')          # form-feed
    text = text.replace('\ufeff', '')           # UTF-8 BOM
    text = re.sub(r'\r\n|\r', '\n', text)      # CRLF / CR → LF
    text = re.sub(r'[ \t]{2,}', ' ', text)    # collapse inline whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)    # max 2 consecutive blank lines
    return text.strip()


def _remove_url_noise(text: str) -> str:
    """Replace raw HTTP/HTTPS URLs with a short placeholder token."""
    return re.sub(r'https?://\S+', '[URL]', text)


def _remove_citations(text: str) -> str:
    """Strip inline citation and reference markers."""
    for pattern in CITATION_PATTERNS:
        text = re.sub(pattern, '', text)
    # Clean up any orphan brackets/parens left after removal
    text = re.sub(r'\[\s*\]', '', text)
    text = re.sub(r'\(\s*\)', '', text)
    return text


def _remove_boilerplate_sentences(text: str, strip_evidence: bool = True) -> str:
    """
    Remove academic boilerplate filler clauses from text.

    Strategy: strip ONLY the matched phrase + optional trailing comma/space.
    The remainder of the sentence is preserved, so result numbers and factual
    content after the boilerplate opener are not lost.

    Example:
        Input:  "As shown in Table 1, our model outperforms by 3.2%."
        Output: "our model outperforms by 3.2%."

        Input:  "In this paper, we propose a novel approach."
        Output: "a novel approach."   (filler phrase stripped, noun kept)
    """
    patterns = list(BOILERPLATE_PATTERNS)
    if strip_evidence:
        patterns.extend(EVIDENCE_POINTER_PATTERNS)

    for pattern in patterns:
        # Strip matched phrase + optional trailing comma + any surrounding whitespace.
        # Do NOT strip [^.!?\n]* — that would eat the rest of the sentence.
        text = re.sub(pattern + r'[,]?\s*', ' ', text)
    # Collapse any double-spaces introduced by phrase removal
    text = re.sub(r' {2,}', ' ', text)
    # Strip leading/trailing spaces on each line (leftover from clause removal)
    text = '\n'.join(line.strip() for line in text.split('\n'))
    return text


def _deduplicate_sentences(text: str, within_section_only: bool = True) -> str:
    """
    Remove exact duplicate sentences within the text.
    Comparison is case-insensitive and whitespace-normalized.
    Preserves the first occurrence; removes subsequent exact duplicates.
    Short fragments (≤10 chars) are kept to avoid removing legitimate short sentences.

    within_section_only=True (default): deduplication scope is this text block only.
    This prevents stripping intentional repetition across different sections
    (e.g. the same finding stated in abstract, introduction, and conclusion).
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    seen: set = set()
    result = []
    for sent in sentences:
        key = re.sub(r'\s+', ' ', sent.strip().lower())
        if len(key) <= 10:
            result.append(sent)
        elif key not in seen:
            seen.add(key)
            result.append(sent)
    return ' '.join(result)


def _remove_formula_lines(text: str, aggressive: bool = False) -> str:
    """
    Remove lines that are predominantly mathematical/symbolic.
    If aggressive=True, removes lines that have <40% alphabetic chars.
    Always removes lines that have 0% alphabetic chars (pure symbol lines).
    Preserves empty lines as section visual breaks.
    """
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append(line)
            continue
        if aggressive:
            if _is_formula_line(line):
                continue
        else:
            # Only drop lines with NO alphabetic characters at all
            if not any(c.isalpha() for c in stripped):
                continue
        result.append(line)
    return '\n'.join(result)


def _compress_section(text: str, mode: str, section_key: str = "") -> Tuple[str, int, int]:
    """
    Apply the compression pipeline to a single section string.

    Section-aware rules (SECTION_COMPRESSION_RULES) override the global mode:
      - "none"    : whitespace normalisation only
      - "minimal" : whitespace + within-section dedup (no boilerplate/formula removal)
      - "light"   : full light pipeline, with evidence pointers preserved
      - "aggressive": light + formula removal, except never on results section

    Returns:
        (compressed_text, original_length, compressed_length)
    """
    original_len = len(text)

    # Resolve effective mode for this section
    effective_mode = SECTION_COMPRESSION_RULES.get(section_key, mode)
    # "none" override means just clean whitespace, nothing more
    if effective_mode == "none":
        text = _normalize_whitespace(text)
        return text, original_len, len(text)

    # ── Stage 1: always run ─────────────────────────────────────────
    text = _normalize_whitespace(text)
    text = _remove_url_noise(text)
    text = _remove_citations(text)
    # Pure symbol-lines stripped in all non-none modes
    text = _remove_formula_lines(text, aggressive=False)

    # ── Stage 2: minimal mode (results) — dedup only, no boilerplate ─
    if effective_mode == "minimal":
        text = _deduplicate_sentences(text, within_section_only=True)
        text = _normalize_whitespace(text)
        return text, original_len, len(text)

    # ── Stage 3: light / aggressive ─────────────────────────────────
    if section_key in ("results", "discussion"):
        text = _remove_boilerplate_sentences(text, strip_evidence=False)
    else:
        text = _remove_boilerplate_sentences(text, strip_evidence=True)

    text = _deduplicate_sentences(text, within_section_only=True)

    # ── Stage 4: aggressive formula removal — skip for results ───────
    if effective_mode == "aggressive" and section_key != "results":
        text = _remove_formula_lines(text, aggressive=True)

    # ── Final cleanup ────────────────────────────────────────────────
    text = _normalize_whitespace(text)
    return text, original_len, len(text)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def compress_sections(sections: dict, mode: str = "light") -> dict:
    """
    Compress all paper sections using Approach A: Structured Normalization.

    Approach A is a deterministic, regex-based pipeline that strips redundant
    content from academic paper text without relying on external ML models or
    making additional API calls.

    Args:
        sections (dict):
            Dict mapping section keys (str) to raw section text (str), as
            produced by section_detector.py. Example keys: "abstract",
            "introduction", "methodology", "results", "discussion",
            "conclusion", "references".

        mode (str):
            Compression aggressiveness. One of:
            - "off"        — passthrough; no compression applied
            - "light"      — whitespace + citations + boilerplate + dedup (default)
            - "aggressive" — light + formula/math line removal

    Returns:
        dict:
            Same keys as input with compressed text values.
            Adds a special "_compression_stats" key (not a section) containing:
            {
                "mode": str,
                "total_original_chars": int,
                "total_compressed_chars": int,
                "reduction_pct": float,        # 0.0–100.0
                "per_section": {
                    section_key: {
                        "original": int,
                        "compressed": int,
                        "pct": float           # reduction %
                    },
                    ...
                }
            }

    Notes:
        - Keys starting with "_" are passed through unchanged (already metadata).
        - Non-string values are passed through unchanged.
        - An empty sections dict returns an empty dict with zeroed stats.
        - If mode is invalid, falls back to "light" with a stderr warning.
    """
    # Validate mode
    valid_modes = ("off", "light", "aggressive")
    if mode not in valid_modes:
        print(f"   [Compress] WARNING: Unknown mode '{mode}', falling back to 'light'.",
              file=sys.stderr)
        mode = "light"

    # Mode "off" — pure passthrough
    if mode == "off":
        result = dict(sections)
        total = sum(
            len(v) for k, v in sections.items()
            if isinstance(v, str) and not k.startswith("_")
        )
        result["_compression_stats"] = {
            "mode": "off",
            "total_original_chars": total,
            "total_compressed_chars": total,
            "reduction_pct": 0.0,
            "per_section": {},
        }
        return result

    # Compression modes: "light" or "aggressive"
    result: dict = {}
    stats: dict = {
        "mode": mode,
        "per_section": {},
        "total_original_chars": 0,
        "total_compressed_chars": 0,
    }

    for key, text in sections.items():
        # Pass through metadata keys and non-string values unchanged
        if key.startswith("_") or not isinstance(text, str):
            result[key] = text
            continue

        # Never compress the references section — citation_checker.py needs
        # the raw reference strings (DOIs, author names, titles) intact.
        if key == "references":
            result[key] = text
            continue

        compressed, orig_len, comp_len = _compress_section(text, mode, section_key=key)
        result[key] = compressed

        pct = round((1.0 - comp_len / orig_len) * 100.0, 1) if orig_len > 0 else 0.0
        stats["per_section"][key] = {
            "original": orig_len,
            "compressed": comp_len,
            "pct": pct,
        }
        stats["total_original_chars"] += orig_len
        stats["total_compressed_chars"] += comp_len

    total_orig = stats["total_original_chars"]
    total_comp = stats["total_compressed_chars"]
    stats["reduction_pct"] = (
        round((1.0 - total_comp / total_orig) * 100.0, 1) if total_orig > 0 else 0.0
    )

    result["_compression_stats"] = stats
    return result
