---
wave: 1
depends_on: []
files_modified:
  - gemini_analyzer.py
  - scoring.py
  - main.py
autonomous: true
requirements:
  - AI-01
  - AI-02
  - AI-03
  - AI-04
  - AI-05
  - AI-06
  - AI-07
  - CORE-05
---

# Phase 2: AI Analysis Engine — Plan

**Phase:** 02 — AI Analysis Engine
**Owner:** Person 2
**Depends on:** Phase 1 (`section_detector.py` sections dict — already complete)
**Goal:** Implement `gemini_analyzer.py` (7 separate Gemini calls, one per layer) and `scoring.py` (pure Python weighted scoring), then wire both into `main.py`.

---

## Canonical References (READ BEFORE STARTING)

- `desirable.md` — Gemini Output Contract section — defines exact JSON per layer
- `.planning/phases/02-ai-analysis-engine/02-CONTEXT.md` — all implementation decisions (D-01 through D-11)
- `ResearchSense_Research.md §3` — the 7 Gemini prompt templates (use these directly, do not redesign)
- `ResearchSense_Research.md §9` — scoring weights and grade mapping
- `.planning/phases/01-environment-pdf-parser/01-CONTEXT.md` — sections dict format from Phase 1
- `main.py` — integration point; the `/analyze` endpoint receives sections and must call analyzer + scorer

---

## must_haves (goal-backward verification)

- [ ] `gemini_analyzer.py` exists and `analyze_paper(sections: dict) -> dict` is callable without error
- [ ] All 7 layers (`grammar`, `readability`, `abstract`, `structure`, `methodology`, `logic`, `conclusion`) are each a **separate** Gemini API call
- [ ] Every layer returns `{"score": int 0-10, "issues": [str], "suggestions": [str]}`
- [ ] Empty section (`""`) → layer returns `{"score": 0, "issues": ["Section not found in document."], "suggestions": ["Add a dedicated section for this component."]}`
- [ ] Invalid Gemini JSON → retry once with strict prompt → on second failure assign `{"score": 0, "issues": ["Analysis unavailable"], "suggestions": ["Retry analysis"]}`
- [ ] `scoring.py` exists and `calculate_score(layer_scores: dict) -> dict` returns `{"final_score": float, "grade": str}`
- [ ] Grade mapping: ≥85→A, ≥70→B, ≥55→C, ≥40→D, <40→F
- [ ] `main.py /analyze` endpoint calls `gemini_analyzer.analyze_paper()` and `scoring.calculate_score()` and returns enriched JSON response

---

## Task 1 — Create `gemini_analyzer.py`

<read_first>
- `ResearchSense_Research.md` (§3 — prompt templates for all 7 layers)
- `.planning/phases/02-ai-analysis-engine/02-CONTEXT.md` (decisions D-01 through D-07)
- `desirable.md` (Gemini Output Contract section — exact output structure required)
- `.env.example` (env var names to use)
</read_first>

<action>
Create `gemini_analyzer.py` in the project root with the following exact structure:

```python
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

EMPTY_RESULT = {
    "score": 0,
    "issues": ["Section not found in document."],
    "suggestions": ["Add a dedicated section for this component."]
}

FALLBACK_RESULT = {
    "score": 0,
    "issues": ["Analysis unavailable — Gemini returned unparseable response."],
    "suggestions": ["Retry the analysis."]
}


def _call_gemini(prompt: str) -> dict:
    """Call Gemini once. On invalid JSON, retry with strict prompt. On second failure return FALLBACK_RESULT."""
    model = genai.GenerativeModel(MODEL)
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.strip())
    except (json.JSONDecodeError, Exception):
        # Retry with strict prompt
        strict_prompt = prompt + "\n\nReturn ONLY valid JSON. No markdown code blocks. No explanatory text."
        try:
            response = model.generate_content(strict_prompt)
            return json.loads(response.text.strip())
        except Exception:
            return FALLBACK_RESULT


def analyze_grammar(text: str) -> dict:
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Analyse the grammar and language quality of the following academic text.
Return ONLY a JSON object with exactly these fields:
{{"score": <integer 0-10>, "issues": [<list of specific grammar/language problems found>], "suggestions": [<list of specific fixes, one per issue>]}}

Text:
{text[:3000]}"""
    return _call_gemini(prompt)


def analyze_readability(text: str) -> dict:
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Analyse the readability of the following academic text. Consider sentence length, vocabulary complexity, clarity, and flow.
Return ONLY a JSON object with exactly these fields:
{{"score": <integer 0-10>, "issues": [<list of specific readability problems>], "suggestions": [<list of specific improvements>]}}

Text:
{text[:3000]}"""
    return _call_gemini(prompt)


def analyze_abstract(text: str) -> dict:
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the quality of this academic paper abstract. Consider whether it states the problem, method, results, and contribution clearly.
Return ONLY a JSON object with exactly these fields:
{{"score": <integer 0-10>, "issues": [<list of specific abstract weaknesses>], "suggestions": [<list of specific improvements>]}}

Abstract:
{text[:2000]}"""
    return _call_gemini(prompt)


def analyze_structure(text: str) -> dict:
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the structural integrity of this academic paper. Consider section organisation, logical flow between sections, and completeness of standard academic structure.
Return ONLY a JSON object with exactly these fields:
{{"score": <integer 0-10>, "issues": [<list of structural problems>], "suggestions": [<list of structural improvements>]}}

Paper content:
{text[:4000]}"""
    return _call_gemini(prompt)


def analyze_methodology(text: str) -> dict:
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the methodology soundness of this academic paper. Consider experimental design, reproducibility, dataset description, and baseline comparisons.
Return ONLY a JSON object with exactly these fields:
{{"score": <integer 0-10>, "issues": [<list of methodology weaknesses>], "suggestions": [<list of specific improvements>]}}

Methodology section:
{text[:3000]}"""
    return _call_gemini(prompt)


def analyze_logic(text: str) -> dict:
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the logical consistency of this academic paper. Check whether claims are supported by evidence, whether conclusions follow from results, and whether there are contradictions between sections.
Return ONLY a JSON object with exactly these fields:
{{"score": <integer 0-10>, "issues": [<list of logical inconsistencies or unsupported claims>], "suggestions": [<list of specific fixes>]}}

Paper content:
{text[:4000]}"""
    return _call_gemini(prompt)


def analyze_conclusion(text: str) -> dict:
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the completeness of this academic paper conclusion. Consider whether it summarises findings, acknowledges limitations, and suggests future work.
Return ONLY a JSON object with exactly these fields:
{{"score": <integer 0-10>, "issues": [<list of conclusion weaknesses>], "suggestions": [<list of specific improvements>]}}

Conclusion section:
{text[:2000]}"""
    return _call_gemini(prompt)


def analyze_paper(sections: dict) -> dict:
    """
    Run all 7 analysis layers on the given sections dict.
    Returns a structured dict with layer_details and layer_scores.

    Args:
        sections: dict with keys: abstract, introduction, methodology,
                  results, discussion, conclusion, references

    Returns:
        {
            "layer_details": {
                "grammar": {"score": int, "issues": [str], "suggestions": [str]},
                ... (same for all 7 layers)
            },
            "layer_scores": {
                "grammar": float,   # 0-10
                "readability": float,
                "abstract": float,
                "structure": float,
                "methodology": float,
                "logic": float,
                "conclusion": float,
                "citations": float  # 0 placeholder — Phase 3 fills this
            }
        }
    """
    full_text = " ".join([v for v in sections.values() if v.strip()])

    layer_details = {
        "grammar":      analyze_grammar(sections.get("introduction", "") + " " + sections.get("methodology", "")),
        "readability":  analyze_readability(full_text),
        "abstract":     analyze_abstract(sections.get("abstract", "")),
        "structure":    analyze_structure(full_text),
        "methodology":  analyze_methodology(sections.get("methodology", "")),
        "logic":        analyze_logic(full_text),
        "conclusion":   analyze_conclusion(sections.get("conclusion", "")),
    }

    layer_scores = {k: float(v.get("score", 0)) for k, v in layer_details.items()}
    layer_scores["citations"] = 0.0  # Phase 3 placeholder

    return {
        "layer_details": layer_details,
        "layer_scores": layer_scores,
    }
```

Key rules from CONTEXT.md to enforce:
- D-01: Use `GEMINI_MODEL` env var only — no fallback model
- D-02: If Gemini call raises exception (429, timeout) → do NOT catch silently; let it bubble to main.py which returns 503
- D-04: Each layer = separate `_call_gemini()` call — do NOT merge layers
- D-06: Empty section string → return EMPTY_RESULT immediately, no API call
</action>

<acceptance_criteria>
- `gemini_analyzer.py` exists in project root
- `python -c "import gemini_analyzer"` exits 0
- `gemini_analyzer.py` contains `def analyze_paper(`
- `gemini_analyzer.py` contains `def analyze_grammar(`
- `gemini_analyzer.py` contains `def analyze_readability(`
- `gemini_analyzer.py` contains `def analyze_abstract(`
- `gemini_analyzer.py` contains `def analyze_structure(`
- `gemini_analyzer.py` contains `def analyze_methodology(`
- `gemini_analyzer.py` contains `def analyze_logic(`
- `gemini_analyzer.py` contains `def analyze_conclusion(`
- `gemini_analyzer.py` contains `EMPTY_RESULT` dict with score=0
- `gemini_analyzer.py` contains `FALLBACK_RESULT` dict
- `gemini_analyzer.py` contains `_call_gemini` with retry logic
</acceptance_criteria>

---

## Task 2 — Create `scoring.py`

<read_first>
- `ResearchSense_Research.md` (§9 — weights and grade mapping)
- `.planning/phases/02-ai-analysis-engine/02-CONTEXT.md` (decisions D-08, D-09)
</read_first>

<action>
Create `scoring.py` in the project root:

```python
# Weights must match desirable.md parameter table and scoring.py WEIGHTS dict
WEIGHTS = {
    "grammar":      0.15,
    "structure":    0.15,
    "methodology":  0.15,
    "logic":        0.15,
    "readability":  0.10,
    "abstract":     0.10,
    "conclusion":   0.10,
    "citations":    0.10,
}

GRADE_MAP = [
    (85, "A — Excellent"),
    (70, "B — Good"),
    (55, "C — Needs Improvement"),
    (40, "D — Poor"),
    (0,  "F — Very Poor"),
]


def calculate_score(layer_scores: dict) -> dict:
    """
    Calculate weighted confidence score (0–100) and letter grade.

    Args:
        layer_scores: dict mapping layer name (str) to score 0–10 (float)
                      Must include: grammar, readability, abstract, structure,
                      methodology, logic, conclusion, citations

    Returns:
        {"final_score": float (0-100), "grade": str}
    """
    confidence_score = sum(
        layer_scores.get(k, 0) * w for k, w in WEIGHTS.items()
    ) * 10

    # Clamp to 0-100
    confidence_score = max(0.0, min(100.0, round(confidence_score, 1)))

    grade = "F — Very Poor"
    for threshold, label in GRADE_MAP:
        if confidence_score >= threshold:
            grade = label
            break

    return {
        "final_score": confidence_score,
        "grade": grade,
    }
```
</action>

<acceptance_criteria>
- `scoring.py` exists in project root
- `python -c "import scoring"` exits 0
- `scoring.py` contains `WEIGHTS` dict with exactly 8 keys
- `scoring.py` contains `def calculate_score(`
- `python -c "import scoring; r = scoring.calculate_score({'grammar':8,'readability':7,'abstract':6,'structure':9,'methodology':7,'logic':8,'conclusion':7,'citations':0}); assert 0 <= r['final_score'] <= 100; assert r['grade'] in ['A — Excellent','B — Good','C — Needs Improvement','D — Poor','F — Very Poor']; print('PASS')"` prints `PASS`
</acceptance_criteria>

---

## Task 3 — Wire into `main.py`

<read_first>
- `main.py` (current state — understand the existing /analyze endpoint flow)
- `gemini_analyzer.py` (just created — understand the return structure)
- `scoring.py` (just created — understand calculate_score signature)
- `.planning/phases/02-ai-analysis-engine/02-CONTEXT.md` (code_context section — exact output shape expected)
</read_first>

<action>
Update `main.py` to call `gemini_analyzer` and `scoring` after section detection.

1. Add imports at top of file (after existing imports):
```python
import gemini_analyzer
import scoring
```

2. In the `/analyze` endpoint, after the `sections = section_detector.detect_sections(text)` line, add:

```python
        # Phase 2: Run AI analysis layers
        try:
            analysis = gemini_analyzer.analyze_paper(sections)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail={"error": "Analysis service unavailable", "message": str(e)}
            )

        # Phase 2: Calculate weighted score
        score_result = scoring.calculate_score(analysis["layer_scores"])
```

3. Update the return statement to include the new fields. Replace the existing `return JSONResponse(...)` with:

```python
        return JSONResponse(content={
            "filename": file.filename,
            "sections": sections,
            "section_count": len([v for v in sections.values() if v.strip()]),
            "warnings": warnings,
            "layer_scores": analysis["layer_scores"],
            "layer_details": analysis["layer_details"],
            "final_score": score_result["final_score"],
            "grade": score_result["grade"],
        })
```
</action>

<acceptance_criteria>
- `main.py` contains `import gemini_analyzer`
- `main.py` contains `import scoring`
- `main.py` contains `gemini_analyzer.analyze_paper(sections)`
- `main.py` contains `scoring.calculate_score(`
- `main.py` contains `"layer_scores"` in the return JSONResponse
- `main.py` contains `"final_score"` in the return JSONResponse
- `main.py` contains `"grade"` in the return JSONResponse
- `python -c "import main"` exits 0 (no import errors)
- Server starts: `uvicorn main:app` exits with startup complete message
</acceptance_criteria>

---

## Verification

### Smoke test (run after all 3 tasks complete)

```bash
# 1. Import checks
python -c "import gemini_analyzer; import scoring; print('Imports OK')"

# 2. Scoring unit test (no API key needed)
python -c "
import scoring
r = scoring.calculate_score({
    'grammar': 8, 'readability': 7, 'abstract': 6,
    'structure': 9, 'methodology': 7, 'logic': 8,
    'conclusion': 7, 'citations': 0
})
assert 0 <= r['final_score'] <= 100, f'Score out of range: {r}'
assert r['grade'] in ['A — Excellent','B — Good','C — Needs Improvement','D — Poor','F — Very Poor']
print(f'Score: {r[\"final_score\"]} | Grade: {r[\"grade\"]} — PASS')
"

# 3. Empty section handling (no API key needed)
python -c "
import gemini_analyzer
r = gemini_analyzer.analyze_grammar('')
assert r['score'] == 0
assert r['issues'][0] == 'Section not found in document.'
print('Empty section handling — PASS')
"

# 4. Server starts (requires API key in .env)
uvicorn main:app --port 8001 &
sleep 3
curl -s http://localhost:8001/ | python -c \"import sys,json; d=json.load(sys.stdin); assert d['status']=='ResearchSense API is running'; print('Server OK')\"
```

### UAT criteria (manual — requires real Gemini API key)

1. POST a real PDF to `/analyze` — response must include `layer_scores`, `layer_details`, `final_score`, `grade`
2. Each of the 7 keys in `layer_details` must have `score`, `issues`, `suggestions`
3. `final_score` must be between 0 and 100
4. `grade` must be one of the 5 valid grade strings
5. A PDF with an empty methodology section must show `score: 0` and `"Section not found in document."` for the methodology layer
