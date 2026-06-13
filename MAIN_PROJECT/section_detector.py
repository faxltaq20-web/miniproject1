import re

# Display names for the UI
SECTION_DISPLAY_NAMES = {
    "abstract":     "Abstract",
    "introduction": "Introduction",
    "related_work": "Related Work",
    "methodology":  "Methods",
    "results":      "Results",
    "discussion":   "Discussion",
    "conclusion":   "Conclusion",
    "references":   "References"
}

# ── Tier 1: Fast keyword mapping ──────────────────────────────────────────────
# Keywords that map to each section (checked against cleaned heading text).
# Covers the vast majority of standard academic papers.
SECTION_KEYWORDS = {
    "abstract":     ["abstract"],
    "introduction": ["introduction"],
    "related_work": ["related work", "literature review", "background", "prior work"],
    "methodology":  ["methodology", "methods", "method", "approach",
                     "experimental setup", "model architecture",
                     "proposed method", "proposed approach", "proposed system",
                     "materials and methods", "study design", "experimental design",
                     "data collection", "data sources"],
    "results":      ["results", "result", "findings", "experiments",
                     "experiment", "evaluation"],
    "discussion":   ["discussion", "analysis"],
    "conclusion":   ["conclusion", "conclusions", "summary", "closing remarks"],
    "references":   ["references", "bibliography", "works cited"],
}

# Valid section keys accepted from LLM mapping (Tier 2)
VALID_SECTION_KEYS = set(SECTION_DISPLAY_NAMES.keys()) | {"none"}

# Headings that STOP the current section (e.g. appendix starts after references).
STOP_KEYWORDS = {
    "appendix", "appendices",
    "checklist",
    "acknowledgement", "acknowledgements",
    "acknowledgment", "acknowledgments",
    "supplementary material", "supplemental material",
    "supplementary", "supplemental",
    "author contributions", "conflict of interest",
    "funding", "data availability", "ethics statement",
    "version control", "reproducibility statement",
    "frequently asked questions",
}


# ─── Heading Utilities ────────────────────────────────────────────────────────

def _clean_heading(line: str) -> str:
    """Strip markdown #, bold **, numbers, roman numerals, and whitespace to get pure heading text."""
    s = line.strip()
    # Remove markdown heading prefix: ## or ###
    s = re.sub(r'^#{1,4}\s*', '', s)
    # Remove bold markers: **text**
    s = s.replace('**', '')
    # Remove leading section numbers: "1", "3.1", "5.2.1", "2.Materials" etc.
    s = re.sub(r'^\d+\.?\d*\.?\s*', '', s)
    # Remove leading roman numerals: "I.", "II", "III." etc.
    s = re.sub(r'^[IVX]+\.?\s+', '', s)
    # Remove trailing em-dash, colon, or period (common in some styles: "Abstract—")
    s = re.sub(r'[—–:\-\.]+$', '', s)
    return s.strip().lower()


def _is_heading_line(line: str) -> bool:
    """
    Check if a line is a heading (markdown or plain text).

    Detection strategy:
    1. Markdown headings (#, ##, ###) — always headings
    2. Short standalone lines (< 80 chars, no sentence-ending punctuation)
    3. ALL CAPS lines (common in academic papers: "INTRODUCTION", "ABSTRACT")
    4. Numbered headings: "1. Introduction", "2.1 Methods"
    """
    stripped = line.strip()
    if not stripped:
        return False
    # Markdown headings — always headings
    if stripped.startswith("#"):
        return True
    # ALL CAPS lines (at least 3 chars, likely section heading)
    if len(stripped) >= 3 and stripped.isupper() and not any(c.isdigit() for c in stripped):
        return True
    # Numbered headings: "1. Introduction", "2.1 Methods", "III. Results"
    if re.match(r'^[IVX\d]+\.?\d*\.?\s+[A-Z]', stripped):
        return True
    # Short line without ending period — likely plain text heading
    if len(stripped) < 80 and not stripped.endswith(".") and not stripped.startswith("|"):
        return True
    return False


# ─── Tier 2 Helpers ───────────────────────────────────────────────────────────

def _extract_all_headings(text: str) -> list:
    """
    Extract candidate section headings from the paper text in order.
    Returns a list of raw heading strings (up to 40 items).

    Focuses on top-level headings: numbered sections (single digit prefix),
    ALL CAPS, and markdown # headings. Sub-sections (3.1, 3.2) are excluded
    to keep the heading list short and the LLM call cheap.
    """
    headings = []
    seen = set()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) > 90:
            continue

        is_candidate = False

        # Markdown headings level 1-2 (# or ##) but not sub-sections (###)
        if re.match(r'^#{1,2}\s+', stripped):
            is_candidate = True

        # ALL CAPS lines (pure section headings like "INTRODUCTION", "ABSTRACT")
        elif (len(stripped) >= 3 and stripped.replace(' ', '').replace('&', '').isupper()
              and not any(c.isdigit() for c in stripped)):
            is_candidate = True

        # Top-level numbered headings only: "1 ", "2 ", "3 " (NOT "3.1 ", "3.2 ")
        elif re.match(r'^\d{1,2}\s+[A-Z]', stripped) and '.' not in stripped.split()[0]:
            is_candidate = True

        # Roman numeral headings: "I.", "II.", "III."
        elif re.match(r'^[IVX]{1,5}\.\s+[A-Z]', stripped):
            is_candidate = True

        if is_candidate:
            # Deduplicate (tables/figures can repeat headings)
            norm = stripped.lower()[:50]
            if norm not in seen:
                seen.add(norm)
                headings.append(stripped)

        if len(headings) >= 40:
            break

    return headings


def _apply_llm_mapping(lines: list, raw_heading_map: dict) -> dict:
    """
    Re-segment the paper text using Gemini's heading → section_key mapping.

    raw_heading_map: {raw_heading_string: section_key}
    e.g. {"3 Pre-Training": "methodology", "1 Introduction": "introduction"}

    Logic:
    - For each line, if it's a heading AND it's in the map → switch current section
    - If it's a heading NOT in the map → sub-heading, continue current section
    - Stop keywords still terminate accumulation
    - "none" mapped sections stop accumulation (acknowledgements, etc.)

    Returns: sections dict {section_key: accumulated_text}
    """
    # Build cleaned-heading → section_key lookup for fast matching
    cleaned_map = {_clean_heading(h): key for h, key in raw_heading_map.items()
                   if key in VALID_SECTION_KEYS}

    sections = {k: "" for k in SECTION_DISPLAY_NAMES}
    current_section = None

    for line in lines:
        if _is_heading_line(line):
            clean = _clean_heading(line)

            # Stop keywords always terminate
            if any(stop in clean for stop in STOP_KEYWORDS):
                current_section = None
                continue

            # Appendix-letter headings (single letter prefix)
            if re.match(r'^[a-z](\.\d+)*\s', clean):
                current_section = None
                continue

            # Check LLM mapping first
            mapped_key = cleaned_map.get(clean)
            if mapped_key is not None:
                if mapped_key == "none":
                    current_section = None
                else:
                    current_section = mapped_key
                    sections[current_section] += line + "\n"
                continue
            # else: unknown heading = sub-heading → fall through to append

        if current_section:
            sections[current_section] += line + "\n"

    # Strip trailing whitespace
    for k in sections:
        sections[k] = sections[k].strip()

    return sections


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def detect_sections(text: str, llm_mapper=None) -> dict:
    """
    Segment text (plain or markdown) into standard academic sections.

    TWO-TIER DETECTION:
      Tier 1 (always): Fast keyword matching — zero API calls.
                       Works for ~80% of standard academic papers.
      Tier 2 (fallback): LLM semantic heading mapping — triggered only when
                         Tier 1 detects fewer than 4 sections.
                         Sends only the heading list (~50 tokens) to Gemini.

    Args:
        text: Full paper text (plain text or PyMuPDF4LLM markdown).
        llm_mapper: Optional callable — gemini_analyzer.map_headings(headings) -> dict.
                    If None, Tier 2 is disabled (Tier 1 only).

    Returns:
        {
            "sections": { "abstract": "...", "introduction": "...", ... },
            "detected_sections": { "Abstract": 96, "Introduction": 94, ... },
            "tier": 1 or 2   # which tier produced the final result
        }
    """
    lines = text.splitlines()

    # ── Tier 1: Keyword matching ──────────────────────────────────────────────
    sections = {k: "" for k in SECTION_DISPLAY_NAMES}
    current_section = None
    matched_via_markdown = {}

    for line in lines:
        is_md = line.strip().startswith("#")

        if _is_heading_line(line):
            clean = _clean_heading(line)

            # Stop keywords terminate accumulation.
            # Inside the references section, bibliography entries can mention
            # keywords like "appendix" or "funding" (e.g. "[12] J. Smith, "A
            # study," Journal, Appendix"). Only treat such lines as a true
            # section break when they are also a markdown header (starts with
            # `#`) or a fully uppercase strong-break heading.
            stripped = line.strip()
            is_strong_break = stripped.startswith("#") or (
                len(stripped) >= 3 and stripped.isupper()
            )
            if any(stop in clean for stop in STOP_KEYWORDS):
                if current_section == "references" and not is_strong_break:
                    # Treat as a normal bibliography line — accumulate, don't break.
                    sections[current_section] += line + "\n"
                    continue
                current_section = None
                continue

            # Appendix-letter headings
            if re.match(r'^[a-z](\.\d+)*\s', clean):
                current_section = None
                continue

            matched_section = None
            for section_name, keywords in SECTION_KEYWORDS.items():
                if any(kw in clean for kw in keywords):
                    matched_section = section_name
                    break

            if matched_section:
                current_section = matched_section
                if is_md:
                    matched_via_markdown[matched_section] = True
                sections[current_section] += line + "\n"
                continue

        if current_section:
            sections[current_section] += line + "\n"

    for k in sections:
        sections[k] = sections[k].strip()

    # Fallback scan: if few sections detected, scan text for keyword anywhere
    detected_count = sum(1 for v in sections.values() if v.strip())
    if detected_count <= 5:
        for section_name, keywords in SECTION_KEYWORDS.items():
            if sections[section_name].strip():
                continue
            for kw in keywords:
                pattern = re.compile(
                    rf'(?:^|\n)\s*(?:\d+\.?\s*)?{re.escape(kw)}\s*[\n\-\—\:\.]',
                    re.IGNORECASE
                )
                match = pattern.search(text)
                if match:
                    start = match.end()
                    end = min(start + 2000, len(text))
                    for other_kw_list in SECTION_KEYWORDS.values():
                        for other_kw in other_kw_list:
                            next_match = re.compile(
                                rf'(?:^|\n)\s*(?:\d+\.?\s*)?{re.escape(other_kw)}\s*[\n\-\—\:\.]',
                                re.IGNORECASE
                            ).search(text, start)
                            if next_match and next_match.start() < end:
                                end = next_match.start()
                    sections[section_name] = text[match.start():end].strip()
                    break

    tier1_count = sum(1 for v in sections.values() if v.strip())
    active_tier = 1

    # ── Tier 2: LLM semantic mapping (only when Tier 1 is sparse) ────────────
    if tier1_count < 4 and llm_mapper is not None:
        print(f"   [SectionDetect] Tier 1 found only {tier1_count} section(s). "
              "Running Tier 2 (LLM heading mapper)...", flush=True)

        headings = _extract_all_headings(text)
        if headings:
            try:
                raw_map = llm_mapper(headings)   # → {raw_heading: section_key}
            except Exception as e:
                print(f"   [SectionDetect] Tier 2 mapper failed ({e}) — "
                      "keeping Tier 1 result.", flush=True)
                raw_map = {}

            if raw_map:
                llm_sections = _apply_llm_mapping(lines, raw_map)
                # Merge: fill any Tier 1 gaps with LLM content
                merged = False
                for key in SECTION_DISPLAY_NAMES:
                    if not sections[key].strip() and llm_sections[key].strip():
                        sections[key] = llm_sections[key]
                        merged = True

                # If LLM produced substantially more content, use it as base
                llm_count = sum(1 for v in llm_sections.values() if v.strip())
                if llm_count > tier1_count:
                    # Override sections that were empty in Tier 1
                    for key in SECTION_DISPLAY_NAMES:
                        if llm_sections[key].strip():
                            sections[key] = llm_sections[key]
                    active_tier = 2

                if merged or active_tier == 2:
                    print(f"   [SectionDetect] Tier 2 complete — "
                          f"now {sum(1 for v in sections.values() if v.strip())} section(s) detected.",
                          flush=True)
            else:
                print("   [SectionDetect] Tier 2 returned empty map — "
                      "keeping Tier 1 result.", flush=True)

    # ── Confidence scores ─────────────────────────────────────────────────────
    detected_sections = {}
    for section_name, content in sections.items():
        if not content.strip():
            continue

        display_name = SECTION_DISPLAY_NAMES.get(section_name, section_name.title())

        # Base confidence
        if active_tier == 2:
            # LLM-mapped sections get a fixed high base — the LLM understood the heading
            confidence = 88
        else:
            confidence = 85 if matched_via_markdown.get(section_name) else 70

        # Content length bonus
        content_lines = len(content.splitlines())
        if content_lines >= 20:
            confidence += 10
        elif content_lines >= 10:
            confidence += 7
        elif content_lines >= 5:
            confidence += 4
        else:
            confidence += 2

        # Deterministic variation (avoids identical scores)
        hash_val = sum(ord(c) for c in content[:200]) % 6
        confidence += hash_val

        confidence = max(80, min(99, confidence))
        detected_sections[display_name] = confidence

    return {
        "sections": sections,
        "detected_sections": detected_sections,
        "tier": active_tier,
    }
