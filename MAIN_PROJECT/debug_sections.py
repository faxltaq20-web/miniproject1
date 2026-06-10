import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pdf_parser, section_detector

pdf = r'C:\Users\mohdf\mini project\MAIN_PROJECT\debug\papers\2201.11903v6.pdf'

print('=== STEP 1: EXTRACTING TEXT ===')
text = pdf_parser.extract_text(pdf)
print(f'Total chars extracted: {len(text)}')
print()

print('=== STEP 2: FIRST 3000 CHARS (raw) ===')
print(text[:3000])
print()
print('--- END OF FIRST 3000 CHARS ---')
print()

print('=== STEP 3: RUNNING SECTION DETECTOR ===')
result = section_detector.detect_sections(text)
sections = result['sections']
detected = result['detected_sections']

print(f'Detected sections: {list(detected.keys())}')
print(f'Confidence scores: {detected}')
print()

print('=== STEP 4: SECTION CONTENT SIZES ===')
for key, content in sections.items():
    stripped = content.strip()
    print(f'  {key:20s}: {len(stripped):6d} chars | {"FOUND" if stripped else "EMPTY"}')

print()
print('=== STEP 5: ALL HEADINGS FOUND IN DOCUMENT (first 150 lines) ===')
lines = text.splitlines()
heading_count = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if not stripped:
        continue
    # Show lines that look like headings
    if stripped.startswith('#') or (len(stripped) < 80 and not stripped.endswith('.') and not stripped.startswith('|') and len(stripped) > 3):
        print(f'  Line {i:4d}: {repr(stripped[:80])}')
        heading_count += 1
        if heading_count >= 60:
            print('  ... (truncated)')
            break
