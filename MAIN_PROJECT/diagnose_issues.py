"""
Diagnostic script for Issue 1 (Section Detection) and Issue 2 (DOI Backtick Bug)
Runs the debug papers through section_detector and citation_checker with detailed logging.
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))

import pdf_parser, section_detector, citation_checker

PAPERS_DIR = os.path.join(os.path.dirname(__file__), "debug", "papers")

def diagnose_section_detection(pdf_path, paper_name):
    """Detailed section detection diagnosis for a single paper."""
    print(f"\n{'='*70}")
    print(f"PAPER: {paper_name}")
    print(f"{'='*70}")

    # Extract text
    text = pdf_parser.extract_text(pdf_path)
    print(f"  Total chars: {len(text)}")
    print(f"  Total lines: {len(text.splitlines())}")

    # Run section detector
    result = section_detector.detect_sections(text)
    sections = result["sections"]
    detected = result["detected_sections"]

    print(f"\n  DETECTED SECTIONS: {list(detected.keys())}")
    print(f"  SECTION COUNT: {len(detected)}")

    # Show section content sizes
    print("\n  SECTION CONTENT SIZES:")
    for key, content in sections.items():
        stripped = content.strip()
        status = "FOUND" if stripped else "EMPTY"
        print(f"    {key:20s}: {len(stripped):6d} chars | {status}")

    # Show what headings are in the document
    print("\n  ALL SHORT LINES (< 80 chars) THAT COULD BE HEADINGS:")
    lines = text.splitlines()
    heading_candidates = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) > 80:
            continue
        # Check if it looks like a heading
        if (stripped.startswith("#") or
            stripped.isupper() and len(stripped) >= 3 or
            re.match(r'^[IVX\d]+\.?\d*\.?\s+[A-Z]', stripped) or
            (len(stripped) < 80 and not stripped.endswith(".") and not stripped.startswith("|"))):
            heading_candidates.append((i, stripped))

    for i, (line_num, heading_text) in enumerate(heading_candidates[:40]):
        safe = heading_text[:80].encode('ascii', errors='replace').decode('ascii')
        print(f"    Line {line_num:4d}: {repr(safe)}")
    if len(heading_candidates) > 40:
        print(f"    ... ({len(heading_candidates)} total candidates)")

    # Test the fallback pattern directly
    print("\n  FALLBACK SCAN TEST:")
    detected_count = sum(1 for v in sections.values() if v.strip())
    print(f"    detected_count = {detected_count} (fallback triggers if <= 1)")

    if detected_count <= 1:
        print("    Fallback SHOULD trigger")
        for section_name, keywords in section_detector.SECTION_KEYWORDS.items():
            if sections[section_name].strip():
                continue
            for kw in keywords:
                pattern = re.compile(
                    rf'(?:^|\n)\s*(?:\d+\.?\s*)?{re.escape(kw)}\s*[\n\-\—\:]',
                    re.IGNORECASE
                )
                match = pattern.search(text)
                if match:
                    context = text[max(0, match.start()-20):match.end()+30]
                    safe = context.encode('ascii', errors='replace').decode('ascii')
                    print(f"    MATCH for '{kw}' in {section_name}: {repr(safe)}")
                else:
                    # Try a looser pattern
                    loose = re.compile(rf'\b{re.escape(kw)}\b', re.IGNORECASE)
                    loose_match = loose.search(text)
                    if loose_match:
                        context = text[max(0, loose_match.start()-20):loose_match.end()+30]
                        safe = context.encode('ascii', errors='replace').decode('ascii')
                        print(f"    LOOSE MATCH for '{kw}' (not fallback): {repr(safe)}")
                    else:
                        print(f"    NO MATCH for '{kw}' in {section_name}")
    else:
        print("    Fallback will NOT trigger (detected_count > 1)")
        # Manually test fallback patterns anyway
        for section_name, keywords in section_detector.SECTION_KEYWORDS.items():
            if sections[section_name].strip():
                continue
            for kw in keywords[:2]:  # Just test first 2 keywords
                pattern = re.compile(
                    rf'(?:^|\n)\s*(?:\d+\.?\s*)?{re.escape(kw)}\s*[\n\-\—\:]',
                    re.IGNORECASE
                )
                match = pattern.search(text)
                if match:
                    context = text[max(0, match.start()-20):match.end()+30]
                    safe = context.encode('ascii', errors='replace').decode('ascii')
                    print(f"    WOULD MATCH for '{kw}' in {section_name}: {repr(safe)}")

    return result


def diagnose_doi_backtick():
    """Test the DOI backtick fix with various edge cases."""
    print(f"\n{'='*70}")
    print("DOI BACKTICK BUG DIAGNOSIS")
    print(f"{'='*70}")

    test_cases = [
        # Case from physics paper
        ("DOI: 10.1007/s10844-017-0473-4`", "10.1007/s10844-017-0473-4"),
        # Unicode smart quotes
        ("DOI: 10.1007/s10844-017-0473-4\u201d", "10.1007/s10844-017-0473-4"),
        ("DOI: 10.1007/s10844-017-0473-4\u2019", "10.1007/s10844-017-0473-4"),
        # Regular quotes
        ('DOI: 10.1007/s10844-017-0473-4"', "10.1007/s10844-017-0473-4"),
        # Mixed
        ("DOI: 10.1007/s10844-017-0473-4`)", "10.1007/s10844-017-0473-4"),
        # No trailing junk
        ("DOI: 10.1007/s10844-017-0473-4", "10.1007/s10844-017-0473-4"),
        # Parentheses around DOI
        ("(DOI: 10.1007/s10844-017-0473-4)", "10.1007/s10844-017-0473-4"),
        # Multiple backticks
        ("DOI: 10.1007/s10844-017-0473-4``", "10.1007/s10844-017-0473-4"),
    ]

    print("\n  Testing _extract_dois with backtick/quote scenarios:")
    all_pass = True
    for input_text, expected_doi in test_cases:
        result = citation_checker._extract_dois(input_text)
        passed = expected_doi in result
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"    [{status}] Input: {repr(input_text)}")
        if not passed:
            print(f"           Expected: {expected_doi}")
            print(f"           Got:      {result}")

    # Test with the actual physics paper references format
    print("\n  Testing with physics paper reference format:")
    physics_ref = """[1] Author, A. (2017). Title of paper. Journal, 12(3), 45-67. https://doi.org/10.1007/s10844-017-0473-4`
[2] Author, B. (2021). Another paper. Journal, 8(1), 12-34. https://doi.org/10.1007/s10444-02109893-4`"""
    result = citation_checker._extract_dois(physics_ref)
    print(f"    Extracted DOIs: {result}")
    for doi in result:
        if doi.endswith("`"):
            print(f"    FAIL: DOI still has trailing backtick: {doi}")
            all_pass = False
        else:
            print(f"    OK: {doi}")

    print(f"\n  OVERALL: {'ALL TESTS PASS' if all_pass else 'SOME TESTS FAILED'}")
    return all_pass


if __name__ == "__main__":
    # Diagnose section detection for each debug paper
    papers = [
        ("cs_ml_2606.06480.pdf", "CS/ML Paper"),
        ("cs_survey_2606.01015.pdf", "CS Survey Paper"),
        ("physics_short_2605.29839.pdf", "Physics Paper"),
        ("bio_medical_2606.02625.pdf", "Bio/Medical Paper"),
        ("econ_social_2606.00614.pdf", "Econ/Social Paper"),
    ]

    for filename, name in papers:
        pdf_path = os.path.join(PAPERS_DIR, filename)
        if os.path.exists(pdf_path):
            diagnose_section_detection(pdf_path, name)
        else:
            print(f"\n  SKIP: {filename} not found")

    # Diagnose DOI backtick bug
    diagnose_doi_backtick()
