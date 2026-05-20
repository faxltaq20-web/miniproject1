import re

SECTION_PATTERNS = {
    "abstract": r"\b(abstract)\b",
    "introduction": r"\b(1\.?\s*introduction|introduction)\b",
    "literature_review": r"\b(2\.?\s*(literature review|related work|background))\b",
    "methodology": r"\b(\d\.?\s*(methodology|methods|method|approach|experimental setup))\b",
    "results": r"\b(\d\.?\s*(results|findings|experiments|evaluation))\b",
    "discussion": r"\b(\d\.?\s*(discussion|analysis))\b",
    "conclusion": r"\b(\d\.?\s*(conclusion|conclusions|summary|closing remarks))\b",
    "references": r"\b(references|bibliography|works cited)\b"
}

def detect_sections(text: str) -> dict:
    """
    Segment plain text into standard academic sections using regex patterns.
    Returns a dictionary mapping section keys to their extracted content strings.
    """
    lines = text.splitlines()
    
    # Initialize output dictionary with all contract keys to guarantee their presence
    sections = {
        "abstract": "",
        "introduction": "",
        "methodology": "",
        "results": "",
        "discussion": "",
        "conclusion": "",
        "references": ""
    }
    # Also track literature_review internally if found
    sections["literature_review"] = ""

    current_section = None

    for line in lines:
        line_lower = line.strip().lower()

        # Check if line matches any section header pattern
        matched_section = None
        for section_name, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, line_lower):
                matched_section = section_name
                break

        if matched_section:
            current_section = matched_section
            # Include the header line itself in the section content
            sections[current_section] += line + "\n"
        elif current_section:
            # Append line to the ongoing active section
            sections[current_section] += line + "\n"

    # Strip trailing whitespace/newlines from accumulated contents
    for k in sections:
        sections[k] = sections[k].strip()

    return sections
