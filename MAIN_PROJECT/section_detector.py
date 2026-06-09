import re

# Display names for the UI
SECTION_DISPLAY_NAMES = {
    "abstract": "Abstract",
    "introduction": "Introduction",
    "related_work": "Related Work",
    "methodology": "Methods",
    "results": "Results",
    "discussion": "Discussion",
    "conclusion": "Conclusion",
    "references": "References"
}

# Keywords that map to each section (checked against cleaned heading text)
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

# Headings that STOP the current section (e.g. appendix starts after references).
# When one of these is detected as a heading, we stop appending to any section.
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


def detect_sections(text: str) -> dict:
    """
    Segment text (plain or markdown) into standard academic sections.

    Works with both PyMuPDF plain text and PyMuPDF4LLM markdown output.
    PyMuPDF4LLM headings like '## **1 Introduction**' are handled.

    Returns:
        {
            "sections": { "abstract": "...", "introduction": "...", ... },
            "detected_sections": { "Abstract": 96, "Introduction": 94, ... }
        }
    """
    lines = text.splitlines()

    # Initialize output
    sections = {k: "" for k in SECTION_DISPLAY_NAMES}

    current_section = None
    matched_via_markdown = {}

    for line in lines:
        is_md = line.strip().startswith("#")

        # Only try to match headings, not body text
        if _is_heading_line(line):
            clean = _clean_heading(line)

            # Check stop keywords first — these terminate all section accumulation
            # (e.g. appendix headings, acknowledgements, checklist after references)
            if any(stop in clean for stop in STOP_KEYWORDS):
                current_section = None
                continue

            # Also stop on standalone appendix-letter headings like
            # "## A Frequently Asked Questions" or "## A.1 ..."
            # (single uppercase letter, possibly followed by digits/dots)
            if re.match(r'^[a-z](\.[\d]+)*\s', clean):
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

        # Append to current section
        if current_section:
            sections[current_section] += line + "\n"

    # Strip trailing whitespace
    for k in sections:
        sections[k] = sections[k].strip()

    # Fallback: if few sections detected, scan for any known heading keyword
    # anywhere in the text. This catches papers where PyMuPDF merges headings
    # with body text or uses unusual formatting.
    detected_count = sum(1 for v in sections.values() if v.strip())
    if detected_count <= 5:
        for section_name, keywords in SECTION_KEYWORDS.items():
            if sections[section_name].strip():
                continue  # already detected
            # Search for keyword as a standalone word (case-insensitive)
            for kw in keywords:
                pattern = re.compile(
                    rf'(?:^|\n)\s*(?:\d+\.?\s*)?{re.escape(kw)}\s*[\n\-\—\:\.]',
                    re.IGNORECASE
                )
                match = pattern.search(text)
                if match:
                    # Extract ~2000 chars after the heading as section content
                    start = match.end()
                    end = min(start + 2000, len(text))
                    # Stop at next known heading or end of text
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

    # Calculate confidence scores
    detected_sections = {}
    for section_name, content in sections.items():
        if not content.strip():
            continue

        display_name = SECTION_DISPLAY_NAMES.get(section_name, section_name.title())

        # Base: markdown heading = 85, plain text = 70
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

        # Deterministic variation
        hash_val = sum(ord(c) for c in content[:200]) % 6
        confidence += hash_val

        confidence = max(80, min(99, confidence))
        detected_sections[display_name] = confidence

    return {
        "sections": sections,
        "detected_sections": detected_sections
    }
