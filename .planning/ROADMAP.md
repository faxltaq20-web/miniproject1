# Phase Roadmap

**Context:** ResearchSense - AI-powered academic paper analysis and error detection system.

| Phase | Goal |
|-------|------|
| [Phase 1: Environment & PDF Parser](#phase-1-environment--pdf-parser) | Set up API scaffolding and extract/segment text from PDFs |
| [Phase 2: AI Analysis Engine](#phase-2-ai-analysis-engine) | Implement the 7-layer Gemini AI evaluations |
| [Phase 3: Citations & Scoring](#phase-3-citations--scoring) | Validate references and compute final weighted scores |
| [Phase 4: Reporting & Web UI](#phase-4-reporting--web-ui) | Generate PDF reports and wire up the final UI |
| [Phase 6: Output Quality Optimization](#phase-6-output-quality-optimization) | Improve analysis accuracy, report quality, and pipeline robustness |
| [Phase 7: Output Consistency and Overall Refinement](#phase-7-output-consistency-and-overall-refinement) | Improve the consistency of LLM analysis outputs and refine all pipeline components and report outputs |


### Phase 5: Gemini 7-Layer AI Analysis Engine

**Goal:** Implement `gemini_analyzer.py` — a single Gemini prompt that returns structured scores, issues, and suggestions for all 7 analysis layers
**Depends on:** Phase 1 (sections dict contract from section_detector.py)

**Requirements Mapped:**
- AI-01: Grammar & Language evaluation (Layer 1)
- AI-02: Readability Score evaluation (Layer 2)
- AI-03: Abstract Quality evaluation (Layer 3)
- AI-04: Structural Integrity evaluation (Layer 4)
- AI-05: Methodology Soundness evaluation (Layer 5)
- AI-06: Logical Consistency evaluation (Layer 6)
- AI-07: Conclusion Completeness evaluation (Layer 7)
- CORE-05: API rate limit handling with exponential backoff

**Success Criteria:**
1. `gemini_analyzer.py` exists and `analyze_paper(sections: dict) -> dict` is callable
2. Single Gemini prompt returns all 7 layers in one API call
3. Each layer returns: `score` (0-10), `issues` (list of str), `suggestions` (list of str)
4. Invalid/timeout responses are caught and return neutral fallback scores
5. Output dict keys match `scoring.py` WEIGHTS keys exactly

**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 5 to break down)

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
- CORE-05: System handles API rate limits with exponential backoff and gracefully degrades on failures

**Success Criteria:**
1. Integration with `google-generativeai` is working and authenticates
2. Each of the 7 layers maps to an independent AI analysis prompt
3. Rate limits are handled properly using exponential backoff/retries
4. Endpoint successfully returns a JSON structure containing 7 layer evaluations
5. Graceful error responses when Gemini returns invalid JSON or times out

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


**Requirements Mapped:**
- REP-02: System generates a structured PDF report using ReportLab
- REP-03: Web UI displays the final score, grade, and breakdown to the user
- REP-04: User can download the generated PDF report

**Success Criteria:**
1. Backend `/analyze` endpoint outputs a downloadable PDF using ReportLab
2. A single-page HTML UI exists with drag-and-drop file support
3. UI presents the score breakdown visually to the user
4. Pre-cached sample results available as demo-day backup

## Phase 6: Output Quality Optimization
**Goal:** Improve analysis accuracy, report quality, and overall pipeline robustness

**Depends on:** Phase 1-4 (core pipeline must be functional)

**Requirements Mapped:**
- OPT-01: Improve LLM prompt quality for more consistent, detailed scoring
- OPT-02: Better handling of non-standard paper structures (review papers, short papers, theses)
- OPT-03: Enhance PDF report layout and readability (spacing, fonts, visual hierarchy)
- OPT-04: Improve citation analysis for papers without DOIs (title-based lookup)
- OPT-05: Add error recovery and graceful degradation for edge cases
- OPT-06: Optimize text truncation strategy for LLM context window usage

**Success Criteria:**
1. Analysis produces consistent scores across repeated runs on the same paper
2. Papers with non-standard sections (e.g., "Background" instead of "Related Work") are correctly parsed
3. PDF report has no clipping, overflow, or layout issues
4. Citation checker handles papers with 0 DOIs gracefully (title-based fallback)
5. Pipeline completes without crashing on any valid PDF input
6. LLM prompt uses full context window efficiently (no wasted tokens)

Plans:
- [x] Plan 1: Prompt Engineering & Scoring Consistency
- [x] Plan 2: Non-Standard Paper Handling
- [x] Plan 3: PDF Report Polish
- [x] Plan 4: Citation Fallback for Zero-DOI Papers
- [x] Plan 5: Error Recovery & Edge Cases

---

## Phase 7: Output Consistency and Overall Refinement
**Goal:** Improve the consistency of LLM analysis outputs and refine all pipeline components and report outputs for production readiness.

**Depends on:** Phase 6 (optimization of the core pipeline must be completed and audited)

**Requirements Mapped:**
- OPT-01: Improve LLM prompt quality for more consistent, detailed scoring
- OPT-03: Enhance PDF report layout and readability (spacing, fonts, visual hierarchy)
- OPT-05: Add error recovery and graceful degradation for edge cases

**Success Criteria:**
1. LLM scoring output is highly consistent across multiple identical runs.
2. Layout alignment, fonts, and spacing are polished across all report types and sizes.
3. Enhanced robustness for complex PDFs with advanced failover mechanisms.

Plans:
- [ ] Plan 1: Deterministic Scoring & Few-Shot Prompting
- [ ] Plan 2: Parallel Citation Title Verification
- [ ] Plan 3: PDF Spacing, Formatting & Safe Keeping
- [ ] Plan 4: API Pre-Flight & Health Checks
