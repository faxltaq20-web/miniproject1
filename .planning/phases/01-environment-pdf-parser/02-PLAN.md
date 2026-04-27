---
phase: 1
plan: 2
title: "Person 2 — AI Analyzer & Scoring Stubs"
owner: "Person 2 (P2)"
wave: 1
depends_on: []
files_modified:
  - gemini_analyzer.py
  - scoring.py
requirements:
  - CORE-04
autonomous: true
---

# Plan 02: Person 2 — AI Analyzer & Scoring Stubs

## Objective

Person 2 creates the stub files for the AI analysis engine and scoring module during Phase 1. These stubs define the public API (function signatures, return types, docstrings) that Person 1's `main.py` will import in Phase 2 integration. The stubs return mock/placeholder data so the codebase stays importable and testable end-to-end even before the real Gemini integration is built in Phase 2.

## Owner

**Person 2 (P2)** — AI Analysis Engine & Scoring

---

## Tasks

### Task 1: Gemini Analyzer Stub (gemini_analyzer.py)

<read_first>
- TEAM_SUMMARY.md (Section 3 — Person 2 Responsibilities)
- ResearchSense_Research.md (Section 3 — Gemini API, Section 6 — Evaluation Parameters)
- .planning/phases/01-environment-pdf-parser/01-CONTEXT.md (Decisions D-10, D-12, D-13)
</read_first>

<action>
Create `gemini_analyzer.py` with:

1. **Imports:** `os`, `json`, `google.generativeai as genai` (but do NOT call Gemini yet — just import)
2. **Constants:**
   ```python
   LAYER_NAMES = [
       "grammar",
       "readability",
       "abstract",
       "structure",
       "methodology",
       "logic",
       "conclusion"
   ]
   ```

3. **`analyze_layer(section_text: str, layer_name: str) -> dict`** — stub function:
   - Docstring: `"""Analyze a single layer using Gemini API. Full implementation in Phase 2."""`
   - Returns a placeholder dict:
     ```python
     return {
         "score": 0,
         "details": f"Layer '{layer_name}' analysis not yet implemented. Coming in Phase 2.",
         "issues_found": [],
         "suggestions": []
     }
     ```

4. **`run_all_layers(sections: dict) -> dict`** — main entry point:
   - Docstring: `"""Run all 7 Gemini analysis layers on the detected sections. Returns dict with layer scores (0-10). Full implementation in Phase 2."""`
   - Iterates over `LAYER_NAMES`
   - Calls `analyze_layer()` for each
   - Returns:
     ```python
     {
         "grammar": {"score": 0, "details": "...", ...},
         "readability": {"score": 0, "details": "...", ...},
         # ... all 7 layers
     }
     ```
   - Logs a message: `print("[Phase 2] AI analysis layers are stubs — returning placeholder scores")`

5. **`configure_gemini() -> None`** — stub that loads API key from env:
   ```python
   def configure_gemini():
       """Configure Gemini API client. Call once at startup."""
       api_key = os.getenv("GEMINI_API_KEY")
       if api_key:
           genai.configure(api_key=api_key)
           print("[Gemini] API configured successfully")
       else:
           print("[Gemini] Warning: GEMINI_API_KEY not found in .env")
   ```
</action>

<acceptance_criteria>
- `gemini_analyzer.py` exists in the project root
- `gemini_analyzer.py` contains `LAYER_NAMES` list with exactly 7 layer names: grammar, readability, abstract, structure, methodology, logic, conclusion
- `gemini_analyzer.py` contains `def analyze_layer(section_text: str, layer_name: str) -> dict`
- `gemini_analyzer.py` contains `def run_all_layers(sections: dict) -> dict`
- `gemini_analyzer.py` contains `def configure_gemini() -> None`
- `run_all_layers({})` returns a dict with all 7 layer names as keys, each with `"score": 0`
- `gemini_analyzer.py` imports `google.generativeai as genai`
- File can be imported without errors: `python -c "import gemini_analyzer"`
</acceptance_criteria>

---

### Task 2: Scoring Module Stub (scoring.py)

<read_first>
- ResearchSense_Research.md (Section 9 — Scoring Algorithm)
- TEAM_SUMMARY.md (Section 4 — Integration Plan, Module Interface Contract)
</read_first>

<action>
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

3. **`calculate_confidence_score(layer_scores: dict) -> dict`** — the real scoring function (can be implemented now since it's pure Python math):
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

This is the REAL implementation — not a stub. The scoring algorithm is pure math with no external dependencies, so Person 2 can build and test it right away in Phase 1.
</action>

<acceptance_criteria>
- `scoring.py` exists in the project root
- `scoring.py` contains `WEIGHTS` dict with 8 entries summing to 1.0
- `scoring.py` contains `GRADE_SCALE` list with 5 grade thresholds
- `scoring.py` contains `def calculate_confidence_score(layer_scores: dict) -> dict`
- `calculate_confidence_score({"grammar": 8, "readability": 7, "abstract": 9, "structure": 8, "methodology": 6, "logic": 7, "conclusion": 8, "citations": 9})` returns `{"final_score": 76.5, "grade": "B — Good", ...}`
- `calculate_confidence_score({})` returns `{"final_score": 0, "grade": "F — Very Poor", ...}`
- File can be imported without errors: `python -c "import scoring"`
</acceptance_criteria>

---

## Verification

### Must-Haves (derived from Phase 1 contribution)
1. ✓ `gemini_analyzer.py` defines the public API that Phase 2 will implement
2. ✓ `scoring.py` has the real weighted scoring algorithm ready to use
3. ✓ Both files are importable without errors
4. ✓ Return types match the interface contract in TEAM_SUMMARY.md Section 4
5. ✓ Scoring function produces correct results for known test cases

### Test Commands
```bash
# Test imports
python -c "import gemini_analyzer; print(gemini_analyzer.LAYER_NAMES)"
python -c "import scoring; print(scoring.calculate_confidence_score({'grammar': 8, 'readability': 7, 'abstract': 9, 'structure': 8, 'methodology': 6, 'logic': 7, 'conclusion': 8, 'citations': 9}))"
```
