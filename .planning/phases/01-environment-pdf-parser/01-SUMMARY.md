---
phase: 01-environment-pdf-parser
plan: 1
subsystem: api
tags: [fastapi, pymupdf, regex]

# Dependency graph
requires: []
provides:
  - requirements.txt and .env.example configuration templates
  - main.py FastAPI application skeleton with /analyze endpoint validating PDFs and handling soft warnings
  - pdf_parser.py extracting plain text via basic PyMuPDF get_text()
  - section_detector.py implementing regex-only segmentation matching shared module interface contract
affects: [02-ai-analysis-scoring, 03-citations-report-frontend]

# Tech tracking
tech-stack:
  added: [fastapi, uvicorn, pymupdf, python-multipart, python-dotenv]
  patterns: [regex-only section segmentation, soft warning generation for missing key sections, fail-fast validation on non-text PDFs]

key-files:
  created: [requirements.txt, .env.example, main.py, pdf_parser.py, section_detector.py]
  modified: [.gitignore]

key-decisions:
  - "Used basic PyMuPDF get_text() instead of pymupdf4llm to keep extraction lean and straightforward for MVP"
  - "Implemented regex-only section detection without Gemini fallback to save API tokens and guarantee fast execution"
  - "Adopted a soft warning approach where missing key sections return empty strings but do not reject the paper analysis flow"

patterns-established:
  - "Regex segmentation: splits lines and accumulates text under matched headers initialized to empty strings"
  - "Graceful extraction failure: returning 422 JSONResponse when pdf_parser raises ValueError on short/scanned texts"

requirements-completed: [CORE-01, CORE-02, CORE-03, CORE-04]

# Metrics
duration: 5min
completed: 2026-05-12
---

# Phase 01 Plan 01: Person 1 — Backend Core & PDF Pipeline Summary

**FastAPI server foundation with basic PyMuPDF text extraction, regex section segmentation, and graceful missing-section warnings**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-12T11:27:22Z
- **Completed:** 2026-05-12T11:32:45Z
- **Tasks:** 4
- **Files modified:** 6

## Accomplishments
- Implemented robust project configuration templates (`requirements.txt`, `.env.example`) excluding unnecessary heavyweight libraries.
- Built clean FastAPI skeleton (`main.py`) orchestrating PDF file validations, temporary storage handling, and JSON responses with soft warnings.
- Crafted lean plain text extractor (`pdf_parser.py`) via `pymupdf.open().get_text()` with validation rejecting scanned or non-text files.
- Designed regex-driven section splitter (`section_detector.py`) ensuring presence of all 7 interface contract keys initialized to empty strings.

## Task Commits

Each task was committed atomically:

1. **Task 1: Project Scaffolding & Dependencies** - `a0f8261`, `75a0066` (feat)
2. **Task 2: FastAPI Application Skeleton (main.py)** - `f85fda7` (feat)
3. **Task 3: PDF Text Extraction (pdf_parser.py)** - `47ad840` (feat)
4. **Task 4: Regex-Only Section Detection (section_detector.py)** - `88a78ae` (feat)

## Files Created/Modified
- `requirements.txt` - Project dependencies tailored for MVP core functionality.
- `.env.example` - Template environment variable file defining model configuration.
- `.gitignore` - Updated to explicitly unignore and track the template `.env.example` file.
- `main.py` - Core FastAPI orchestrator hosting the `/analyze` endpoint.
- `pdf_parser.py` - Simple and effective PyMuPDF plain text extraction module.
- `section_detector.py` - Rule-based regex academic section segmentation matching shared contract.

## Decisions Made
- Chose basic PyMuPDF `get_text()` over `pymupdf4llm` to avoid Markdown conversion complexities and unnecessary library footprint.
- Rely strictly on regular expressions for academic section headings, dropping multi-model or AI-based fallbacks to guarantee fast responses and predictability.
- Implemented soft warnings instead of hard validation rejections for missing critical paper sections to maintain testability and let subsequent layers evaluate partial content.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - backend foundation cleanly assembled and verified against the MVP specification.

## User Setup Required

None - no external service configuration required for Person 1 deliverables (API keys are needed for subsequent AI/scoring phases).

## Next Phase Readiness
- Backend core API, extraction module, and section detector are completely built and documented.
- Ready for Person 2 (`gemini_analyzer.py`, `scoring.py`) and Person 3 (`citation_checker.py`, `report_generator.py`) to integrate their respective implementations into `main.py`.
