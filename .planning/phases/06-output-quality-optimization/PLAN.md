# Phase 6 — Output Quality Optimization: PLAN

**Phase Goal:** Improve analysis accuracy, report quality, and pipeline robustness

---

## Plan 1: Prompt Engineering & Scoring Consistency (OPT-01, OPT-06)

**Files:** `gemini_analyzer.py`

### Tasks:
1. **Refine the combined prompt** — add scoring rubric with explicit criteria per score band (0-3: poor, 4-6: average, 7-8: good, 9-10: excellent) so the LLM scores consistently
2. **Add examples** — include 1-2 few-shot examples in the prompt showing expected JSON output format
3. **Optimize text truncation** — instead of blind `[:8000]`, use smart truncation:
   - Abstract: full text
   - Introduction: full text
   - Methodology: full text
   - Results: first 2000 chars
   - Discussion/Conclusion: full text
   - References: skip (handled by citation_checker)
4. **Score clamping** — if LLM returns a score outside 0-10, clamp it

### Verification:
- Run the same paper 3 times → scores should differ by ≤1 point per layer
- Total text sent to LLM should be within model's context window

---

## Plan 2: Non-Standard Paper Handling (OPT-02)

**Files:** `section_detector.py`

### Tasks:
1. **Expand keyword mappings** — add common alternatives:
   - "Literature Review" → related_work
   - "Experimental Results" → results  
   - "Research Design" → methodology
   - "Implications" → discussion
   - "Final Remarks" → conclusion
   - "Proposed Framework" / "System Design" → methodology
2. **Partial match support** — if a heading *contains* a keyword (not exact match), still detect it with lower confidence
3. **Subsection grouping** — roll up subsections like "3.1 Data Collection", "3.2 Analysis" under their parent section ("3 Methodology")

### Verification:
- Test with the sample paper (Attention Is All You Need) → should detect 7+ sections
- Test with a heading like "Experimental Results and Discussion" → should map to "results"

---

## Plan 3: PDF Report Polish (OPT-03)

**Files:** `report_generator.py`

### Tasks:
1. **Fix score text clipping** — ensure "/ 25" never overflows card boundaries (already partially fixed, verify)
2. **Improve progress bar labels** — show percentage text inside or beside the bar
3. **Better spacing** — add consistent vertical spacing between sections
4. **Truncate long issues/suggestions** — if text overflows a card, truncate with "..." to prevent layout breaks
5. **Empty section handling** — if a layer has 0 issues, show "No issues found" instead of empty space

### Verification:
- Generate test PDF with `generate_test_pdf.py` → visually inspect all sections
- No text should overflow card boundaries

---

## Plan 4: Citation Fallback for Zero-DOI Papers (OPT-04)

**Files:** `citation_checker.py`

### Tasks:
1. **Count reference lines** — even without DOIs, count how many `[1]`, `[2]`... style references exist
2. **Minimum reference threshold** — if paper has <5 references, flag as "insufficient references"
3. **Partial credit** — give partial citation score based on reference count even without DOI verification:
   - 0 refs → 0/10
   - 1-5 refs → 3/10
   - 6-15 refs → 5/10
   - 16+ refs → 7/10 (remaining 3 points still require DOI verification)
4. **Better messaging** — when 0 DOIs found, show "No DOIs detected — score based on reference count" instead of just 0

### Verification:
- Test with a paper that has no DOIs but has numbered references → should get partial score
- Test with a paper that has DOIs → should work as before

---

## Plan 5: Error Recovery & Edge Cases (OPT-05)

**Files:** `run_local.py`, `main.py`, `gemini_analyzer.py`

### Tasks:
1. **Catch PDF extraction errors** — if PyMuPDF4LLM fails, fall back to plain PyMuPDF `get_text()`
2. **Handle empty sections** — if section_detector finds 0 sections, still run analysis on full text
3. **LLM timeout handling** — if Gemini doesn't respond in 60s, return fallback scores
4. **Malformed JSON recovery** — if LLM returns partial JSON, try to extract whatever scores are present
5. **Report generation safety** — wrap report generation in try/catch so analysis results are still returned even if PDF fails

### Verification:
- Test with a very short PDF (< 1 page) → should not crash
- Test with a scanned PDF (no text) → should show clear error message
- Kill network mid-analysis → should return fallback scores

---

## Execution Order

```
Plan 1 (Prompt Engineering)     — highest impact on output quality
  ↓
Plan 2 (Non-Standard Papers)    — improves section detection
  ↓
Plan 4 (Citation Fallback)      — fixes 0-score citation problem
  ↓
Plan 3 (Report Polish)          — visual improvements
  ↓
Plan 5 (Error Recovery)         — robustness hardening
```

**Estimated effort:** ~2-3 hours total
