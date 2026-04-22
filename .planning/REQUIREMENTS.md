# Requirements: ResearchSense

**Defined:** 2026-04-22
**Core Value:** Upload a research paper PDF and instantly get a detailed, multi-dimensional quality analysis with actionable feedback — so students know exactly what to fix before submitting to a journal or professor.

## v1 Requirements

### Core Pipeline
- [ ] **CORE-01**: User can upload a PDF research paper via Web UI
- [ ] **CORE-02**: System extracts text from the PDF using PyMuPDF (with OCR fallback)
- [ ] **CORE-03**: System segments extracted text into standard academic sections
- [ ] **CORE-04**: FastAPI backend orchestrates the full analysis pipeline

### AI Analysis Engine
- [ ] **AI-01**: System evaluates Grammar & Language (Layer 1) via Gemini API
- [ ] **AI-02**: System evaluates Readability Score (Layer 2) via Gemini API
- [ ] **AI-03**: System evaluates Abstract Quality (Layer 3) via Gemini API
- [ ] **AI-04**: System evaluates Structural Integrity (Layer 4) via Gemini API
- [ ] **AI-05**: System evaluates Methodology Soundness (Layer 5) via Gemini API
- [ ] **AI-06**: System evaluates Logical Consistency (Layer 6) via Gemini API
- [ ] **AI-07**: System evaluates Conclusion Completeness (Layer 7) via Gemini API

### Citations & Validation
- [ ] **CITE-01**: System extracts citations and references from the paper
- [ ] **CITE-02**: System verifies citation existence/credibility via Semantic Scholar API
- [ ] **CITE-03**: System validates DOIs via CrossRef API

### Scoring & Reporting
- [ ] **REP-01**: System calculates a weighted confidence score (0-100) and letter grade
- [ ] **REP-02**: System generates a structured PDF report using ReportLab
- [ ] **REP-03**: Web UI displays the final score, grade, and breakdown to the user
- [ ] **REP-04**: User can download the generated PDF report

## v2 Requirements

### (None currently deferred)

## Out of Scope

| Feature | Reason |
|---------|--------|
| User accounts/login | Anyone can upload; not needed for university demo |
| Paper storage/history | Privacy-first; analyze and discard files immediately |
| Mobile application | Web-first is sufficient for the target audience |
| Plagiarism detection | Outside the scope of structural and qualitative analysis |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 0 | Pending |
| CORE-02 | Phase 0 | Pending |
| CORE-03 | Phase 0 | Pending |
| CORE-04 | Phase 0 | Pending |
| AI-01 | Phase 0 | Pending |
| AI-02 | Phase 0 | Pending |
| AI-03 | Phase 0 | Pending |
| AI-04 | Phase 0 | Pending |
| AI-05 | Phase 0 | Pending |
| AI-06 | Phase 0 | Pending |
| AI-07 | Phase 0 | Pending |
| CITE-01 | Phase 0 | Pending |
| CITE-02 | Phase 0 | Pending |
| CITE-03 | Phase 0 | Pending |
| REP-01 | Phase 0 | Pending |
| REP-02 | Phase 0 | Pending |
| REP-03 | Phase 0 | Pending |
| REP-04 | Phase 0 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 0
- Unmapped: 18 ⚠️

---
*Requirements defined: 2026-04-22*
*Last updated: 2026-04-22 after initial definition*
