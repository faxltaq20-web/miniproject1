# ResearchSense

## What This Is

ResearchSense is an AI-powered academic paper analysis and error detection system. Students upload a research paper PDF, and the system automatically evaluates it across 8 quality dimensions — grammar, readability, abstract quality, structure, methodology, logic, conclusion, and citations — then generates a structured PDF report with a confidence score (0–100) and a letter grade. This is a university mini-project graded by an external professor.

## Core Value

Upload a research paper PDF and instantly get a detailed, multi-dimensional quality analysis with actionable feedback — so students know exactly what to fix before submitting to a journal or professor.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] PDF upload and text extraction (PyMuPDF with OCR fallback)
- [ ] Automatic section detection (regex-based with Gemini AI fallback)
- [ ] 8-layer analysis engine (Gemini API for layers 1-7, Semantic Scholar + CrossRef for layer 8)
- [ ] Weighted scoring algorithm producing 0-100 confidence score with letter grade
- [ ] Structured PDF report generation (ReportLab)
- [ ] Web UI with drag-and-drop upload and results display
- [ ] FastAPI backend orchestrating the full pipeline
- [ ] Citation verification via Semantic Scholar API
- [ ] DOI validation via CrossRef API
- [ ] Rate limit handling with retry logic for all external APIs

### Out of Scope

- Mobile app — web-first, sufficient for university demo
- User authentication/accounts — not needed for v1, anyone can upload
- Paper storage/history — analyze and discard, no database needed
- Real-time collaboration — single-user analysis flow
- Plagiarism detection — separate domain, not part of this project

## Context

- University mini-project guided by professor, graded by external examiner from another university
- Target users: university students analyzing research papers before submission
- Students want to know: "Will my paper get approved?" — the scoring and feedback should frame results in terms of approval readiness
- All external APIs are free tier (Gemini, Semantic Scholar, CrossRef)
- Gemini 2.5 Flash is the primary AI model (free tier: 250 RPD, 10 RPM)
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
| Gemini 2.5 Flash as primary AI engine | Free tier, 1M token context, strong JSON output | — Pending |
| PyMuPDF for PDF extraction | Best free option for native PDFs, OCR fallback available | — Pending |
| FastAPI for backend | Python-native, async file uploads, auto-generated docs | — Pending |
| Simple HTML/CSS/JS frontend | Sufficient for university demo, no framework complexity | — Pending |
| ReportLab for PDF reports | Free, Python-native, professional output | — Pending |
| 8-layer weighted scoring (specific weights in research doc) | Research-backed criteria from peer review standards | — Pending |

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
*Last updated: 2026-04-21 after initialization*
