# Phase 1: Environment & PDF Parser - Context

**Gathered:** 2026-04-26
**Updated:** 2026-05-11 — simplified to MVP scope
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the complete project foundation: virtual environment, modular file structure, API key management, FastAPI skeleton with `/analyze` endpoint, PDF text extraction via pymupdf4llm, and section detection with Gemini fallback. This phase ends when a PDF can be uploaded and the system returns a JSON response with detected sections.

**What this phase does NOT include:** AI analysis layers (Phase 2), citation checking (Phase 3), report generation or frontend UI (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### PDF Extraction
- **D-01:** Use **basic PyMuPDF `get_text()`** for text extraction — simple, reliable, no additional dependencies
- **D-02:** `pymupdf4llm` (Markdown pipeline) is **not used** — unnecessary complexity for MVP
- **D-03:** **No OCR, no scanned PDF handling** — text-based PDFs only. If a PDF yields no text, return a simple error: "Could not extract text from this PDF. Please ensure it is a text-based PDF." This is MVP scope; OCR is future scope.

### Section Detection
- **D-04:** **Regex-only** detection on the plain text extracted by PyMuPDF — no Gemini fallback
- **D-05:** Gemini fallback for section detection is **removed** — it wastes API quota and regex on academic papers is sufficient for MVP
- **D-06:** **No strict rejection gate** — if some sections are missing, proceed with what was found and let the analysis layers handle partial content. Warn the user which sections were not detected but do not block analysis.
- **D-07:** Section detection output is a best-effort dict — missing sections are empty strings `""`; downstream layers skip or score 0 for missing sections

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
- **D-12:** **Single Gemini model only** (`GEMINI_MODEL=gemini-2.5-flash`) — if the API call fails, return a clear error immediately: "Analysis service temporarily unavailable. Please try again." No Flash-Lite fallback, no multi-model orchestration — MVP keeps it simple.
- **D-13:** When Gemini returns unparseable/invalid JSON: retry that specific layer **once** with a stricter prompt suffix: "Return ONLY valid JSON. No markdown code blocks. No explanatory text." If retry also fails → mark that layer as 0/10 and continue with remaining layers.

### Future Scope (not in MVP)
- `pymupdf4llm` Markdown extraction pipeline
- Gemini fallback for section detection
- OCR / scanned PDF support (Tesseract)
- Strict structural validation / multi-level rejection logic
- Multi-model Gemini orchestration (Flash → Flash-Lite fallback)

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

- Missing sections produce a **soft warning** in the response, not a hard rejection — analysis proceeds with available sections
- Model names stored as env vars means switching from Flash to Flash-Lite (or any future model) requires only a `.env` change, no code changes
- Regex on plain `get_text()` output is sufficient for MVP — academic papers have predictable heading patterns

</specifics>

<deferred>
## Deferred Ideas

- **pymupdf4llm / Markdown extraction pipeline** — Deferred to future scope. Basic `get_text()` is sufficient for MVP.
- **Gemini fallback for section detection** — Deferred to future scope. Regex-only for now.
- **OCR for scanned PDFs** — Future scope. Text-based PDFs only for MVP.
- **Strict structural rejection (missing section gate)** — Future scope. MVP proceeds with best-effort section detection.
- **Multi-level fallback systems** — Future scope.

</deferred>

---

*Phase: 01-environment-pdf-parser*
*Context gathered: 2026-04-26*
*Last updated: 2026-05-11 — simplified to MVP (basic PyMuPDF, regex-only section detection, no Gemini fallback, no OCR, no strict rejection)*
