# Phase Roadmap

**Context:** ResearchSense - AI-powered academic paper analysis and error detection system.

| Phase | Goal |
|-------|------|
| [Phase 1: Environment & PDF Parser](#phase-1-environment--pdf-parser) | Set up API scaffolding and extract/segment text from PDFs |
| [Phase 2: AI Analysis Engine](#phase-2-ai-analysis-engine) | Implement the 7-layer Gemini AI evaluations |
| [Phase 3: Citations & Scoring](#phase-3-citations--scoring) | Validate references and compute final weighted scores |
| [Phase 4: Reporting & Web UI](#phase-4-reporting--web-ui) | Generate PDF reports and wire up the final UI |

---

## Phase 1: Environment & PDF Parser
**Goal:** Set up API scaffolding and extract/segment text from PDFs

**Requirements Mapped:**
- CORE-01: User can upload a PDF research paper via Web UI
- CORE-02: System extracts text from the PDF using PyMuPDF (with OCR fallback)
- CORE-03: System segments extracted text into standard academic sections
- CORE-04: FastAPI backend orchestrates the full analysis pipeline

**Success Criteria:**
1. FastAPI app starts and accepts a PDF upload on `/analyze`
2. PyMuPDF successfully extracts raw text
3. Section parsing splits text using regex (with Gemini fallback capability)
4. JSON payload returns identified sections gracefully

## Phase 2: AI Analysis Engine
**Goal:** Implement the 7-layer Gemini AI evaluations

**Requirements Mapped:**
- AI-01: System evaluates Grammar & Language (Layer 1) via Gemini API
- AI-02: System evaluates Readability Score (Layer 2) via Gemini API
- AI-03: System evaluates Abstract Quality (Layer 3) via Gemini API
- AI-04: System evaluates Structural Integrity (Layer 4) via Gemini API
- AI-05: System evaluates Methodology Soundness (Layer 5) via Gemini API
- AI-06: System evaluates Logical Consistency (Layer 6) via Gemini API
- AI-07: System evaluates Conclusion Completeness (Layer 7) via Gemini API

**Success Criteria:**
1. Integration with `google-generativeai` is working and authenticates
2. Each of the 7 layers maps to an independent AI analysis prompt
3. Rate limits are handled properly using wait/retries
4. Endpoint successfully returns a JSON structure containing 7 layer evaluations.

## Phase 3: Citations & Scoring
**Goal:** Validate references and compute final weighted scores

**Requirements Mapped:**
- CITE-01: System extracts citations and references from the paper
- CITE-02: System verifies citation existence/credibility via Semantic Scholar API
- CITE-03: System validates DOIs via CrossRef API
- REP-01: System calculates a weighted confidence score (0-100) and letter grade

**Success Criteria:**
1. CrossRef validation parses DOIs from references correctly
2. Semantic Scholar API effectively queries titles to evaluate citations
3. The 8 metrics are unified to compute the final letter grade and confidence score

## Phase 4: Reporting & Web UI
**Goal:** Generate PDF reports and wire up the final UI

**UI hint:** yes

**Requirements Mapped:**
- REP-02: System generates a structured PDF report using ReportLab
- REP-03: Web UI displays the final score, grade, and breakdown to the user
- REP-04: User can download the generated PDF report

**Success Criteria:**
1. Backend `/analyze` endpoint outputs a downloadable PDF using ReportLab
2. A single-page HTML UI exists with drag-and-drop file support
3. UI presents the score breakdown visually to the user
