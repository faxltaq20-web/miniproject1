"""
Diagnostic: Compare PyMuPDF vs PyMuPDF4LLM extraction on sample_paper.pdf
Shows what sections are detected and what's missed with each approach.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pymupdf

# ── Step 1: Current approach (PyMuPDF plain text) ─────────────────
print("=" * 60)
print("  METHOD 1: PyMuPDF (current) — plain text extraction")
print("=" * 60)

doc = pymupdf.open("sample_paper.pdf")
plain_text = ""
for page in doc:
    plain_text += page.get_text()
doc.close()

print(f"\nTotal chars extracted: {len(plain_text)}")
print(f"Total lines: {len(plain_text.splitlines())}")

# Run section detector on it
import section_detector
result1 = section_detector.detect_sections(plain_text)
sections1 = result1["sections"]
detected1 = result1["detected_sections"]

print(f"\nDetected {len(detected1)} sections:")
for name, conf in detected1.items():
    text_len = 0
    # find matching section key
    for k, v in sections1.items():
        display = section_detector.SECTION_DISPLAY_NAMES.get(k, k.title())
        if display == name:
            text_len = len(v)
            break
    print(f"  {name:20s}  {conf}%  ({text_len} chars)")

# Show what's missing
all_expected = set(section_detector.SECTION_DISPLAY_NAMES.values())
found = set(detected1.keys())
missing = all_expected - found
if missing:
    print(f"\n  MISSING sections: {', '.join(missing)}")
else:
    print(f"\n  All 8 standard sections detected!")

# Show first 5 lines of raw text to see what headers look like
print(f"\n--- First 30 lines of raw text ---")
for i, line in enumerate(plain_text.splitlines()[:30]):
    line_stripped = line.strip()
    if line_stripped:
        print(f"  {i+1:3d}: {line_stripped[:80]}")

# ── Step 2: Try PyMuPDF4LLM (if installed) ────────────────────────
print("\n" + "=" * 60)
print("  METHOD 2: PyMuPDF4LLM — markdown extraction")
print("=" * 60)

try:
    import pymupdf4llm
    md_text = pymupdf4llm.to_markdown("sample_paper.pdf")
    
    print(f"\nTotal chars extracted: {len(md_text)}")
    print(f"Total lines: {len(md_text.splitlines())}")
    
    # Count markdown headings
    headings = [l.strip() for l in md_text.splitlines() if l.strip().startswith("#")]
    print(f"\nMarkdown headings found: {len(headings)}")
    for h in headings[:20]:
        print(f"  {h[:80]}")
    
    # Run section detector on markdown text too
    result2 = section_detector.detect_sections(md_text)
    detected2 = result2["detected_sections"]
    sections2 = result2["sections"]
    
    print(f"\nDetected {len(detected2)} sections:")
    for name, conf in detected2.items():
        text_len = 0
        for k, v in sections2.items():
            display = section_detector.SECTION_DISPLAY_NAMES.get(k, k.title())
            if display == name:
                text_len = len(v)
                break
        print(f"  {name:20s}  {conf}%  ({text_len} chars)")
    
    found2 = set(detected2.keys())
    missing2 = all_expected - found2
    if missing2:
        print(f"\n  MISSING sections: {', '.join(missing2)}")
    else:
        print(f"\n  All 8 standard sections detected!")
        
except ImportError:
    print("\n  pymupdf4llm not installed. Installing...")
    print("  Run: pip install pymupdf4llm")
    print("  Then re-run this script to compare.")

print("\n" + "=" * 60)
print("  VERDICT")
print("=" * 60)
