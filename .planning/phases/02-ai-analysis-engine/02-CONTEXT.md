# Phase 2: AI Analysis Engine - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the 7 Gemini-powered analysis layers and the pure-Python weighted scoring algorithm. This phase takes the sections dict from Phase 1 and produces a scored JSON result per layer plus a final confidence score (0–100) with letter grade.

**What this phase does NOT include:** Citation checking (Phase 3), report generation or frontend UI (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### Gemini Usage — What Gemini IS and IS NOT Used For

**Gemini IS used for (core value of the project):**
- **Layer 1:** Grammar & Language analysis
- **Layer 2:** Readability Score evaluation
- **Layer 3:** Abstract Quality assessment
- **Layer 4:** Structural Integrity review
- **Layer 5:** Methodology Soundness evaluation
- **Layer 6:** Logical Consistency check
- **Layer 7:** Conclusion Completeness assessment

**Gemini is NOT used for (replaced with Python/regex):**
- **Section splitting** — already handled by regex in Phase 1
- **Citation extraction** — regex on the References section text
- **Score calculation** — pure Python weighted average math
- **Placeholder/stub analysis** — no fake Gemini calls; implement each layer properly or not at all

### Gemini API Setup
- **D-01:** **Single model only** — `GEMINI_MODEL=gemini-2.5-flash` from `.env`. No fallback model, no multi-model orchestration.
- **D-02:** If a Gemini API call fails (429, timeout, error) → return a clear error immediately: "Analysis service temporarily unavailable. Please try again." Fail fast, no retry chain.
- **D-03:** If Gemini returns **invalid/unparseable JSON** → retry that layer **once** with a stricter prompt: "Return ONLY valid JSON. No markdown code blocks. No explanatory text." If still invalid → assign 0/10 for that layer and continue.
- **D-04:** Each of the 7 layers is a **separate API call** — do not combine layers into a single prompt (harder to parse, harder to debug, harder to assign individual scores).

### Analysis Layers — Implementation
- **D-05:** Each layer sends its specific section(s) to Gemini with a targeted prompt and expects a JSON response containing: `{"score": int (0-10), "issues": [str], "suggestions": [str]}`
- **D-06:** If a section is an empty string `""` (not detected in Phase 1) → skip that layer, assign 0/10, add a note: "Section not found in document."
- **D-07:** Prompts come from `ResearchSense_Research.md §3` — use those directly, no need to redesign them

### Score Calculation — Pure Python
- **D-08:** Scoring is **pure Python math** — no Gemini involvement:
  ```python
  weights = {
      "grammar": 0.15, "readability": 0.10, "abstract": 0.10,
      "structure": 0.15, "methodology": 0.15, "logic": 0.15,
      "conclusion": 0.10, "citations": 0.10
  }
  confidence_score = sum(layer_scores[k] * weights[k] for k in weights) * 10
  ```
- **D-09:** Grade mapping (pure Python dict lookup):
  ```python
  if score >= 85: grade = "A — Excellent"
  elif score >= 70: grade = "B — Good"
  elif score >= 55: grade = "C — Needs Improvement"
  elif score >= 40: grade = "D — Poor"
  else: grade = "F — Very Poor"
  ```

### Citation Extraction (Layer 8 prep for Phase 3)
- **D-10:** Citation extraction from the References section = **regex on plain text** — no Gemini. Extract DOIs (`10.XXXX/...` pattern) and reference titles using string parsing.
- **D-11:** Phase 2 defines the interface; Phase 3 implements the API calls. The citations layer score (0/10 default) is a placeholder that Phase 3 fills in.

### Agent's Discretion
- Exact prompt wording for each layer (use ResearchSense_Research.md §3 as the base)
- Whether to call all 7 layers sequentially or use async (sequential is fine for MVP)
- Timeout value for each Gemini API call

### Future Scope (not in MVP)
- Multi-model Gemini orchestration (Flash → Flash-Lite fallback)
- Combining multiple layers into a single Gemini call for efficiency
- Async/concurrent Gemini calls across all 7 layers
- Gemini-assisted citation extraction or validation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Primary user (professors), report tone, constraints
- `.planning/REQUIREMENTS.md` — AI-01 through AI-07 are this phase's requirements
- `.planning/phases/01-environment-pdf-parser/01-CONTEXT.md` — Phase 1 decisions, especially the sections dict format that Phase 2 receives

### Technical Research
- `ResearchSense_Research.md` — Key sections for this phase:
  - §3 — All 7 Gemini prompt templates (use these directly)
  - §9 — Scoring algorithm weights and grading scale
  - §10 — FastAPI integration points

</canonical_refs>

<code_context>
## Existing Code Insights

### Integration Points
- Phase 2 receives sections dict from Phase 1 in this format:
  ```python
  sections = {
      "abstract": str,      # "" if not detected
      "introduction": str,
      "methodology": str,
      "results": str,
      "discussion": str,
      "conclusion": str,
      "references": str
  }
  ```
- Phase 2 outputs to `main.py`:
  ```python
  analysis_result = {
      "layer_scores": {
          "grammar": float,      # 0-10
          "readability": float,
          "abstract": float,
          "structure": float,
          "methodology": float,
          "logic": float,
          "conclusion": float,
          "citations": float     # 0 placeholder; Phase 3 fills this
      },
      "layer_details": {
          "grammar": {"score": int, "issues": [str], "suggestions": [str]},
          # ... same structure for all layers
      },
      "final_score": float,      # 0-100
      "grade": str               # "A — Excellent", "B — Good", etc.
  }
  ```

</code_context>

<specifics>
## Specific Ideas

- Keep each layer as an independent function: `analyze_grammar(text)`, `analyze_readability(text)`, etc. — this makes testing and debugging straightforward
- The scoring function is completely decoupled from Gemini — it just takes a dict of 0-10 scores and returns the weighted result
- Phase 3 (citations) slots into the `layer_scores["citations"]` key — Phase 2 leaves it at 0 until Phase 3 is ready

</specifics>

<deferred>
## Deferred Ideas

- **Multi-model fallback** — Future scope. Single model only for MVP.
- **Gemini for citation extraction** — Future scope. Regex handles this for MVP.
- **Async concurrent Gemini calls** — Future scope. Sequential is fine for MVP.
- **Combined multi-layer Gemini prompts** — Future scope. One call per layer for MVP.

</deferred>

---

*Phase: 02-ai-analysis-engine*
*Context gathered: 2026-05-11*
