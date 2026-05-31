---
phase: 1
plan: 2
title: "Person 2 — Scoring Module"
owner: "Person 2 (P2)"
wave: 1
depends_on: []
files_modified:
  - scoring.py
requirements:
  - CORE-04
autonomous: true
---

# Plan 02: Person 2 — Scoring Module

## Objective

Person 2 builds the real scoring module (`scoring.py`) during Phase 1. This is pure Python math — no Gemini, no external APIs. The scoring function is the single source of truth for all grade calculations. The real Gemini analysis layers (`gemini_analyzer.py`) will be built in Phase 2 — no placeholder stubs are created here.

## Owner

**Person 2 (P2)** — AI Analysis Engine & Scoring

---

## Tasks

### Task 1: Scoring Module (scoring.py)

**Read first:**
- `ResearchSense_Research.md` (Section 9 — Scoring Algorithm)
- `TEAM_SUMMARY.md` (Section 4 — Integration Plan, Module Interface Contract)
- `02-CONTEXT.md` (Decisions D-08, D-09)

**Action:**

Create `scoring.py` with:

1. **`WEIGHTS` constant** — the official weight configuration:
   ```python
   WEIGHTS = {
       "grammar":      0.15,
       "readability":  0.10,
       "abstract":     0.10,
       "structure":    0.15,
       "methodology":  0.15,
       "logic":        0.15,
       "conclusion":   0.10,
       "citations":    0.10
   }
   ```

2. **`GRADE_SCALE` constant:**
   ```python
   GRADE_SCALE = [
       (85, "A — Excellent"),
       (70, "B — Good"),
       (55, "C — Needs Improvement"),
       (40, "D — Poor"),
       (0,  "F — Very Poor")
   ]
   ```

3. **`calculate_confidence_score(layer_scores: dict) -> dict`** — the real scoring function:
   ```python
   def calculate_confidence_score(layer_scores: dict) -> dict:
       """
       Calculate the weighted confidence score from layer scores.

       Args:
           layer_scores: dict with keys matching WEIGHTS, values 0-10

       Returns:
           dict with final_score (0-100), grade, layer_breakdown, weights_used
       """
       if not layer_scores:
           return {"final_score": 0, "grade": "F — Very Poor", "layer_breakdown": {}, "weights_used": WEIGHTS}

       weighted_sum = 0
       for layer, weight in WEIGHTS.items():
           score = layer_scores.get(layer, 0)
           weighted_sum += score * weight

       final_score = round(weighted_sum * 10, 1)

       grade = "F — Very Poor"
       for threshold, grade_label in GRADE_SCALE:
           if final_score >= threshold:
               grade = grade_label
               break

       return {
           "final_score": final_score,
           "grade": grade,
           "layer_breakdown": {k: round(v * 10, 1) for k, v in layer_scores.items()},
           "weights_used": WEIGHTS
       }
   ```

> This is the **REAL implementation** — not a stub. Pure Python math, no external dependencies. Person 2 can build and test this right away in Phase 1.

**Acceptance criteria:**
- `scoring.py` exists in the project root
- `scoring.py` contains `WEIGHTS` dict with 8 entries summing to 1.0
- `scoring.py` contains `GRADE_SCALE` list with 5 grade thresholds
- `scoring.py` contains `def calculate_confidence_score(layer_scores: dict) -> dict`
- Test: `calculate_confidence_score({"grammar": 8, "readability": 7, "abstract": 9, "structure": 8, "methodology": 6, "logic": 7, "conclusion": 8, "citations": 9})` returns `{"final_score": 76.5, "grade": "B — Good", ...}`
- Test: `calculate_confidence_score({})` returns `{"final_score": 0, "grade": "F — Very Poor", ...}`
- File imports without errors: `python -c "import scoring"`

---

## Verification

### Must-Haves
1. ✓ `scoring.py` has the real weighted scoring algorithm
2. ✓ `scoring.py` is importable without errors
3. ✓ Return types match the interface contract in `TEAM_SUMMARY.md` Section 4
4. ✓ Scoring function produces correct results for known test cases
5. ✓ `gemini_analyzer.py` is NOT created in Phase 1 — real implementation is Phase 2

### Test Commands
```bash
# Test scoring
python -c "import scoring; print(scoring.calculate_confidence_score({'grammar': 8, 'readability': 7, 'abstract': 9, 'structure': 8, 'methodology': 6, 'logic': 7, 'conclusion': 8, 'citations': 9}))"

# Expected output: final_score: 76.5, grade: B — Good
```
