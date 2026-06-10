import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pdf_parser, section_detector

pdf = r'C:\Users\mohdf\mini project\MAIN_PROJECT\debug\papers\2201.11903v6.pdf'

text = pdf_parser.extract_text(pdf)
result = section_detector.detect_sections(text)
sections = result['sections']
detected = result['detected_sections']

print('=== SECTION DETECTION AFTER FIX ===')
print(f'Detected: {list(detected.keys())}')
print()

before = {
    'abstract':     2196,
    'introduction': 7234,
    'related_work': 1752,
    'methodology':  6112,
    'results':      17012,
    'discussion':   2872,
    'conclusion':   951,
    'references':   107257,
}
new_limits = {
    'abstract':     2000,
    'introduction': 3000,
    'related_work': 1500,
    'methodology':  4000,
    'results':      4000,
    'discussion':   2500,
    'conclusion':   1500,
}

print(f'  {"Section":<20} {"Before (chars)":>16} {"After (chars)":>15} {"Sent to LLM":>13} {"Coverage":>10}')
print('  ' + '-'*76)
for key in ['abstract','introduction','related_work','methodology','results','discussion','conclusion','references']:
    content = sections.get(key, '').strip()
    new_chars = len(content)
    old_chars = before.get(key, 0)
    limit = new_limits.get(key, 0)
    sent = min(new_chars, limit) if limit else '-'
    sent_str = f'{sent:,}' if isinstance(sent, int) else sent
    coverage = f'{sent/new_chars*100:.0f}%' if isinstance(sent, int) and new_chars > 0 else 'N/A'
    delta = f'*** FIXED: -{old_chars - new_chars:,}' if key == 'references' and new_chars != old_chars else ''
    print(f'  {key:<20} {old_chars:>16,} {new_chars:>15,} {sent_str:>13} {coverage:>10}  {delta}')

total_sent = sum(min(len(sections.get(k,'').strip()), new_limits[k]) for k in new_limits)
print()
print(f'  Total sent to LLM  : {total_sent:,} chars  (~{total_sent//4:,} tokens)')
print(f'  Old total sent     : 11,500 chars  (~2,875 tokens)')
print(f'  Improvement        : +{total_sent - 11500:,} chars  ({(total_sent/11500 - 1)*100:.0f}% more content)')
