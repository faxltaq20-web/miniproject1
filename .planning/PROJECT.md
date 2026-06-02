# ResearchSense

## What This Is

ResearchSense is an AI-powered academic paper analysis and error detection system. Professors and students upload a research paper PDF, and the system automatically evaluates it across 8 quality dimensions — grammar, readability, abstract quality, structure, methodology, logic, conclusion, and citations — then generates a structured PDF report with a confidence score (0–100) and a letter grade. The primary user is a **university professor** working with students on research papers — the report acts as a formal review instrument the professor can use to assess readiness for submission. Students are secondary users who self-check their own work. This is a university mini-project graded by an external professor.

## Core Value

Give professors an instant, objective review instrument — upload a paper and get a structured multi-dimensional quality report that identifies exactly what is missing or weak, so professors can make informed decisions on whether students are ready to submit.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [x] PDF upload and text extraction (basic PyMuPDF & smart PyMuPDF4LLM)
- [x] Automatic section detection (with high-fidelity fallback & confidence scores)
- [x] 8-layer analysis engine (restructured to 5-layer premium matching reference UI)
- [x] Weighted scoring algorithm producing 0-100 confidence score with letter grade
- [x] Structured PDF report generation (ReportLab PLATYPUS cover page & custom flowables)
- [ ] Web UI with drag-and-drop upload and results display
- [x] FastAPI backend orchestrating the full pipeline
- [x] Citation verification via Semantic Scholar Title Search
- [x] DOI validation via CrossRef API
- [x] Rate limit handling with retry logic & auto-backoff for all external APIs
- [x] Graceful error handling and diagnostics (/health endpoint)

### Out of Scope

- Mobile app — web-first, sufficient for university demo
- User authentication/accounts — not needed for v1, anyone can upload
- Paper storage/history — analyze and discard, no database needed
- Real-time collaboration — single-user analysis flow
- Plagiarism detection — separate domain, not part of this project

## Context

- University mini-project guided by professor, graded by external examiner from another university
- **Primary users:** University professors reviewing student research papers before journal/conference submission
- **Secondary users:** Students self-checking their own work before submitting to their professor
- Report tone must be formal and clinical — a review instrument for professors, not coaching feedback for students
- **Team:** 3 people — work divided by module ownership, combined via GitHub
  - P1: Backend core (`main.py`, `pdf_parser.py`, `section_detector.py`)
  - P2: AI engine + scoring (`gemini_analyzer.py`, `scoring.py`)
  - P3: Citations + report + frontend (`citation_checker.py`, `report_generator.py`, `frontend/`)
- All external APIs are free tier (Gemini, CrossRef)
- Gemini 2.5 Flash is the single AI model (no fallback)
- Timeline: ~1.5 months to completion
- Detailed technical research already completed (ResearchSense_Research.md)
- Python ecosystem throughout — FastAPI, PyMuPDF, ReportLab, google-generativeai

## Constraints

- **Budget**: Zero — all tools and APIs must be free tier
- **AI Model**: Gemini 2.5 Flash (free tier limits: 250 RPD, 10 RPM, 250K TPM)
- **Tech Stack**: Python backend (FastAPI), HTML/CSS/JS frontend — as specified in research document
- **Timeline**: ~1.5 months until external evaluation
- **Demo**: Must work reliably for live demo to external professor — pre-cache sample results as backup

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Gemini 2.5 Flash as primary AI engine | Free tier, 1M token context, strong JSON output | — Approved |
| PyMuPDF for PDF extraction | Best free option for native PDFs, OCR fallback available | — Approved |
| FastAPI for backend | Python-native, async file uploads, auto-generated docs | — Approved |
| Simple HTML/CSS/JS frontend | Sufficient for university demo, no framework complexity | — Active |
| ReportLab for PDF reports | Free, Python-native, professional output | — Approved |
| 8-layer weighted scoring | Restructured to 5-layer premium matching reference UI | — Approved |
| Upgraded to PyMuPDF4LLM | Restructure text extraction for smarter markdown parsing | — Approved |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-26 after Phase 1 discussion — primary user updated to professors*
