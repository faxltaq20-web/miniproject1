CHARS_PER_TOKEN = 4

sections = {
    'abstract':     2196,
    'introduction': 7234,
    'related_work': 1752,
    'methodology':  6112,
    'results':      17012,
    'discussion':   2872,
    'conclusion':   951,
    'references':   107257,
}

print('=== PAPER SECTION SIZES ===')
total = 0
for name, chars in sections.items():
    tokens = chars // CHARS_PER_TOKEN
    total += chars
    print(f'  {name:20s}: {chars:7,} chars = ~{tokens:5,} tokens')
print(f'  {"TOTAL":20s}: {total:7,} chars = ~{total//CHARS_PER_TOKEN:5,} tokens')

print()
print('=== CURRENT LIMITS in gemini_analyzer.py ===')
current = {
    'abstract':     2000,
    'introduction': 2000,
    'related_work': 1000,
    'methodology':  2500,
    'results':      1500,
    'discussion':   1500,
    'conclusion':   1000,
}
current_total = sum(current.values())
print(f'  Per-section sum : {current_total:,} chars = ~{current_total//CHARS_PER_TOKEN:,} tokens')
print(f'  MAX_TOTAL cap   : 12,000 chars = ~3,000 tokens')
print(f'  % of paper seen : {round(current_total/total*100, 1)}%')

print()
print('=== SMART PROPOSED LIMITS ===')
smart = {
    'abstract':     2000,
    'introduction': 3000,
    'related_work': 1500,
    'methodology':  4000,
    'results':      4000,
    'discussion':   2500,
    'conclusion':   1500,
}
prompt_overhead = 2000
smart_total = sum(smart.values())
grand_total = smart_total + prompt_overhead
print(f'  Per-section sum : {smart_total:,} chars = ~{smart_total//CHARS_PER_TOKEN:,} tokens')
print(f'  Prompt overhead : {prompt_overhead:,} chars = ~{prompt_overhead//CHARS_PER_TOKEN:,} tokens')
print(f'  GRAND TOTAL     : {grand_total:,} chars = ~{grand_total//CHARS_PER_TOKEN:,} tokens')

print()
print('=== GEMINI 2.5 FLASH FREE TIER ===')
tpm = 250000
rpd = 500
tokens_per_call = grand_total // CHARS_PER_TOKEN
print(f'  TPM limit             : {tpm:,} tokens/min')
print(f'  Tokens per paper call : ~{tokens_per_call:,} tokens')
print(f'  Papers per minute     : {tpm // tokens_per_call} papers (well within limit)')
print(f'  RPD limit             : {rpd} requests/day (the real bottleneck)')
print(f'  Time per paper        : ~15-25 seconds (slightly slower, acceptable)')

print()
print('=== VERDICT ===')
print('  Sending 18,500 chars (~4,600 tokens) per paper is TOTALLY FEASIBLE.')
print('  The bottleneck is RPD (500 req/day), NOT token size.')
print('  Tripling the content sent = same RPD cost, just richer analysis.')
print()
print('  What we should NOT do: send the full 145K chars (references included)')
print('  That wastes tokens on bibliography text and doesnt help scoring.')
print('  Smart limits per section = best of both worlds.')
