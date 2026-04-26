# Phase 1: Environment & PDF Parser - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the complete project foundation: virtual environment, modular file structure, API key management, FastAPI skeleton with `/analyze` endpoint, PDF text extraction via pymupdf4llm, and section detection with Gemini fallback. This phase ends when a PDF can be uploaded and the system returns a JSON response with detected sections.

**What this phase does NOT include:** AI analysis layers (Phase 2), citation checking (Phase 3), report generation or frontend UI (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### PDF Extraction
- **D-01:** Use `pymupdf4llm` (Markdown output) as the **primary** extraction method — preserves heading structure which makes section detection significantly more reliable
- **D-02:** Fall back to `pymupdf` basic `get_text()` only if `pymupdf4llm` fails/throws an exception
- **D-03:** **No OCR** — scanned PDFs (no extractable text) are rejected with a clear error message: "This appears to be a scanned PDF. Please upload a text-based PDF." No Tesseract dependency needed.

### Section Detection
- **D-04:** Regex-based detection runs first on the Markdown output from pymupdf4llm
- **D-05:** Gemini AI fallback triggers **only if fewer than 3 sections are detected** by regex — this is the threshold check: `if len(sections) < 3: use_gemini_fallback()`
- **D-06:** Minimum required sections for analysis to proceed: **Abstract + Methodology + Conclusion**. If any of these three are missing after detection, reject the paper immediately.
- **D-07:** Rejection response includes: (a) clear error message listing exactly which sections are missing, (b) a note informing the user that a sample format PDF is available — actual sample PDF generation is deferred to Phase 4 (ReportLab)

### Project Layout
- **D-08:** Modular from day 1 — one file per responsibility, mirroring the team split:
  ```
  main.py              ← FastAPI orchestrator (P1)
  pdf_parser.py        ← pymupdf4llm extraction (P1)
  section_detector.py  ← regex + Gemini fallback (P1)
  gemini_analyzer.py   ← 7 Gemini layers (P2)
  scoring.py           ← weighted score algorithm (P2)
  citation_checker.py  ← Semantic Scholar + CrossRef (P3)
  report_generator.py  ← ReportLab PDF (P3)
  frontend/            ← HTML/CSS/JS (P3)
  ```
- **D-09:** `main.py` acts as the single orchestrator — imports from all modules, owns the `/analyze` endpoint

### API Key & Configuration Management
- **D-10:** All secrets and config in `.env` via `python-dotenv`. Variables to define:
  ```
  GEMINI_API_KEY=
  GEMINI_MODEL_PRIMARY=gemini-2.5-flash
  GEMINI_MODEL_FALLBACK=gemini-2.5-flash-lite
  CONTACT_EMAIL=          ← used for CrossRef polite pool
  ```
- **D-11:** `.env` is in `.gitignore` — already set up. Each team member uses their own API key locally.

### Error Handling & API Resilience
- **D-12:** API failure chain: Try `GEMINI_MODEL_PRIMARY` → on failure (429, error), try `GEMINI_MODEL_FALLBACK` → if both fail, return clear error: "Analysis service temporarily unavailable. Please try again in a few minutes."
- **D-13:** When Gemini returns unparseable/invalid JSON: retry that specific layer **once** with a stricter prompt suffix: "Return ONLY valid JSON. No markdown code blocks. No explanatory text." If retry also fails → mark that layer as 0/10 and continue with remaining layers.

### Team & Collaboration
- **D-14:** Team of 3, each owning one module group (P1/P2/P3 as above)
- **D-15:** GitHub for collaboration — each person works on their module, integrates on one device when development is complete
- **D-16:** `.gitignore` already created and committed — `.env` is protected

### Agent's Discretion
- Exact regex patterns for section detection (the research doc has good starting patterns — use them)
- FastAPI CORS configuration details
- Exact retry logic / sleep timing for the model fallback chain
- How to structure the `sections` dict returned by `section_detector.py`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Project vision, primary user (professors), team split, constraints
- `.planning/REQUIREMENTS.md` — Full v1 requirements with REQ-IDs (CORE-01 through CORE-04 are this phase)

### Technical Research
- `ResearchSense_Research.md` — Complete technical spec with code templates for every component:
  - Section 3: Gemini API setup and prompt templates
  - Section 4: PyMuPDF extraction code (basic + pymupdf4llm)
  - Section 5: Section detection regex patterns and Gemini fallback
  - Section 10: FastAPI skeleton with `/analyze` endpoint structure
  - Section 14: Installation & setup guide, project structure

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet — this is Phase 1, greenfield

### Established Patterns
- None yet — patterns established here become the standard for Phase 2 and 3

### Integration Points
- `main.py /analyze` endpoint → calls `pdf_parser.py` → calls `section_detector.py` → returns sections JSON
- Phase 2 (`gemini_analyzer.py`) will import section dict from Phase 1's `section_detector.py` output format — make sure the dict keys are consistent: `{"abstract": str, "introduction": str, "methodology": str, "results": str, "conclusion": str, "references": str}`

</code_context>

<specifics>
## Specific Ideas

- The rejection message for missing sections should be **professor-facing and formal** — e.g., "Structural validation failed: The following required sections were not detected: [Methodology]. Papers must contain Abstract, Methodology, and Conclusion to proceed with analysis."
- Model names stored as env vars means switching from Flash to Flash-Lite (or any future model) requires only a `.env` change, no code changes
- The `< 3 sections` Gemini fallback threshold was chosen to save API quota — regex on pymupdf4llm Markdown output should handle 95%+ of standard academic PDFs without needing Gemini

</specifics>

<deferred>
## Deferred Ideas

- **Sample format PDF for rejected papers** — Decided to include this feature, but the PDF generation deferred to Phase 4 (ReportLab is scoped there). Phase 1 returns the text error only.
- **OCR for scanned PDFs** — Deliberately excluded. Fail gracefully instead. Can be revisited post-submission if needed.

</deferred>

---

*Phase: 01-environment-pdf-parser*
*Context gathered: 2026-04-26*
