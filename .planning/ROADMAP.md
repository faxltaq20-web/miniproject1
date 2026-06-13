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
| [Phase 8: Web Frontend Dashboard](#phase-8-web-frontend-dashboard) | Implement the premium client-facing Web UI dashboard with glassmorphic aesthetics, dynamic steppers, SVGs, diagnostics, and interactive PDF downloading |
| [Phase 9: Automated End-to-End Debugging](#phase-9-automated-end-to-end-debugging) | Auto-fetch real academic papers, run the full pipeline with Gemini AI API, and validate nothing is missing |
| [Phase 10: API Token Efficiency & Input Compression](#phase-10-api-token-efficiency--input-compression) | Reduce Gemini API token usage by ≥40% via structured text normalization and semantic compression without score drift |
| [Phase 11: Improve the frontend UI](#phase-11-improve-the-frontend-ui) | Improve the frontend UI layout, interactive dashboard widgets, styling, and user experience |
| [Phase 12: Improve citation detection](#phase-12-improve-citation-detection) | Improve citation detection |

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

**Plans:** 1 plans

Plans:

- [x] Plan 1: Gemini 7-Layer AI Analysis Engine (merged with Phase 6)

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

- [x] Plan 1: Deterministic Scoring & Few-Shot Prompting
- [x] Plan 2: Parallel Citation Title Verification
- [x] Plan 3: PDF Spacing, Formatting & Safe Keeping
- [x] Plan 4: API Pre-Flight & Health Checks

---

## Phase 8: Web Frontend Dashboard

**Goal:** Implement the premium client-facing Web UI dashboard with glassmorphic aesthetics, dynamic steppers, SVGs, diagnostics, and interactive PDF downloading.

**Depends on:** Phase 7 (optimized and deterministic backend APIs must be operational)

**Requirements Mapped:**

- REP-03: Web UI displays the final score, grade, and breakdown to the user
- REP-04: User can download the generated PDF report

**Success Criteria:**

1. A single-page, highly responsive HTML/CSS/JS frontend dashboard exists inside `frontend/`.
2. Fully interactive file upload supporting drag-and-drop and strict `.pdf` validation.
3. Multi-stage visual stepper dynamically showing the 5 backend processing steps.
4. Beautiful score gauge SVG and Grade Pill displaying the final evaluation score.
5. Interactive, expandable multi-layer accordion cards showing raw scores, weights, specific issues (red) and suggestions (green) for the 5 active layers.
6. A scrollable citation list displaying metadata tooltips for verified citations and clear badges for flagged issues.
7. Prominent "Download PDF Report" action button that POSTs current results to `/report` and triggers immediate binary browser download.
8. Interactive pre-cached "Try Sample" mock dashboard for API-free grading demo.
9. Footnote diagnostic badge displaying real-time API health status calling `/health`.

Plans:

- [x] Plan 1: UI Mockup & Static Pages Scaffolding
- [x] Plan 2: Modern Glassmorphic Design System (CSS)
- [x] Plan 3: Client Orchestration & API Connectivity (JS)
- [x] Plan 4: PDF Downloading & Offline Mock Demo

---

## Phase 9: Automated End-to-End Debugging

**Goal:** Build an automated test harness that fetches real academic papers from open-access sources (arXiv, Semantic Scholar OA), runs each through the full ResearchSense pipeline (PDF parse → section detect → Gemini AI analysis → citation check → scoring → report generation), and validates that nothing is missing, broken, or inconsistent — catching bugs across diverse paper types before demo day.

**Depends on:** Phase 8 (all pipeline and UI components must be operational)

**Requirements Mapped:**

- DEBUG-01: Automated paper fetcher pulls real PDFs from arXiv and Semantic Scholar Open Access APIs
- DEBUG-02: Full pipeline runner executes /analyze and /report endpoints against each fetched paper
- DEBUG-03: Output validator checks response schemas, score ranges, section detection completeness, and report PDF integrity
- DEBUG-04: Gap analysis compares pipeline output against paper metadata (expected sections, citation counts, DOI presence) to flag missing coverage
- DEBUG-05: Regression test suite records baseline results and detects score drift across runs
- DEBUG-06: Summary report aggregates pass/fail/warning counts across all test papers with detailed diagnostics

**Success Criteria:**

1. Test harness fetches ≥5 diverse real papers automatically (CS, medicine, social science, review papers, short papers)
2. Each paper runs through the full `/analyze` → `/report` pipeline without crashes
3. All response JSON schemas match expected structure (layer_scores, layer_details, citation_result, final_score, grade)
4. Score values are within valid ranges (0-10 per layer, 0-100 final score, valid grade letters)
5. Section detection handles diverse paper structures (non-standard headings, missing sections) gracefully
6. Citation checker correctly processes papers with and without DOIs
7. PDF report generation succeeds for all test papers without layout errors
8. Gap analysis identifies any layers returning fallback/default scores and flags them
9. Summary report produced with per-paper pass/fail status and aggregate statistics

**Plans:** 4 plans

Plans:

- [ ] Plan 1: Real Paper Fetcher — arXiv & Semantic Scholar OA
- [ ] Plan 2: Full Pipeline Runner — `/analyze` + `/report` per Paper
- [ ] Plan 3: Output Validator & Gap Analyzer — Schema + Completeness Checks
- [ ] Plan 4: Summary Report Generator — Human-Readable Diagnostic Output

---

## Phase 10: API Token Efficiency & Input Compression

**Goal:** Reduce the number of tokens sent to the Gemini API per paper analysis call — without losing the semantic content needed for accurate scoring — by applying a structured text normalization and compression pipeline on extracted paper sections before they are assembled into the LLM prompt.

**Depends on:** Phase 9 (baseline pipeline must be fully validated so we have ground-truth output to compare against)

---

### 🧩 Formal Problem Definition

**Problem Statement:**

Given a set of extracted academic paper sections *S = {s₁, s₂, ..., sₙ}* (abstract, introduction, methodology, etc.) where total character count *|S| ≫ 20,000*, design a lossless-semantic compression function *f(S) → S'* such that:

1. **|S'| ≪ |S|** — the compressed representation is significantly shorter in token count
2. **sem(S') ≈ sem(S)** — the semantic content relevant for scoring is fully preserved
3. **score(f(S)) ≈ score(S)** — Gemini's output scores and issues when given *S'* closely match those it produces for *S* (within ±0.5 per layer, measured on a validation set)

This is formally known in NLP literature as **"prompt compression"** or **"context distillation for LLM inference"** — a subproblem of *information-preserving text reduction*.

---

### 📐 Why This Matters (Current Numbers)

From `token_budget.py` analysis:

- A real paper sends ~**150,000 chars** (the `MAX_TOTAL` cap in `gemini_analyzer.py`)
- Even with smart per-section limits, we send ~**18,500 chars ≈ 4,625 tokens** of paper content
- The Gemini free-tier bottleneck is **500 RPD** — NOT token count per call
- BUT: larger prompts increase latency (~15–25 sec/paper), risk context overflow on smaller models, and cost more on paid tiers
- Reducing input size by **40–60%** would cut per-call latency and allow future migration to cheaper, smaller models (e.g., `gemini-1.5-flash-8b`)

---

### 🔬 Candidate Approaches (Research-Ready)

**Approach A — Structured Normalization (Recommended First)**
> *Research keyword: "extractive prompt compression"*

Transform each section into a normalized, shorter but semantically-equivalent representation:

- Strip boilerplate phrases: "In this paper, we...", "It is worth noting that..."
- Collapse whitespace, remove footnote markers, fix OCR noise
- Deduplicate repeated sentences (common in methodology/results sections)
- Keep only topic sentences of each paragraph (extractive summarization)
- **Expected reduction: 30–50%** with zero LLM cost

**Approach B — Semantic Chunking + Key Sentence Extraction**
> *Research keyword: "extractive summarization for RAG / prompt engineering"*

Use `sentence-transformers` or `spacy` to score each sentence by relevance to the evaluation criteria (structure, clarity, methodology, evidence) and keep only top-K sentences per section:

- Each section → top 5–10 most "review-relevant" sentences
- Assembles a compact, information-dense "review digest"
- **Expected reduction: 60–75%** with high semantic fidelity

**Approach C — LLM-Based Compression (Meta-Prompt)**
> *Research keyword: "LLM prompt compression / selective context compression (LLMLingua)"*

Send the full text to a cheap/fast LLM first, asking it to produce a "review digest" in structured format, then send THAT digest to the main scorer:

- Two-stage pipeline: compress → score
- Uses `LLMLingua` (Microsoft Research, open source) or a cheap Gemini Flash call for compression
- **Expected reduction: 70–80%** but adds one extra API call (may not save quota)

**Approach D — Template-Driven Section Summarization**
> *Research keyword: "information extraction for structured summarization"*

Instead of sending raw section text, extract structured key facts:

- Abstract → `{objective, method, results, contribution}`
- Methodology → `{dataset, model, baselines, metrics, training_details}`
- Results → `{primary_metric, comparison_table, key_numbers}`
- Format these as compact structured text blocks, not prose
- **Expected reduction: 50–65%**, highly deterministic, no external dependencies

**Requirements Mapped:**

- OPT-06: Optimize text truncation strategy for LLM context window usage (existing)
- TOKEN-01: Design and implement a text normalization pre-processor that reduces prompt size by ≥40% with <5% semantic loss
- TOKEN-02: Validate compressed output against uncompressed baseline on 5 real papers (score delta ≤0.5 per layer)
- TOKEN-03: Make compression strategy configurable (off / light / aggressive) via `.env`

**Success Criteria:**

1. New `text_compressor.py` module with `compress_sections(sections: dict, mode: str) → dict` interface
2. Compression reduces total assembled prompt by ≥40% (measured in chars) in default `light` mode
3. Score drift vs. uncompressed baseline is ≤0.5 per layer on ≥4 of 5 validation papers
4. Pipeline latency (time from upload to result) improves by ≥20% in `aggressive` mode
5. Zero regressions on existing Phase 9 test suite (all passing papers still pass)

**Plans:** 3 plans

Plans:

- [x] Plan 1: Text Normalization & Extractive Pre-Processor (`text_compressor.py`)
- [x] Plan 2: Validation Harness — Score Drift & Token Reduction Metrics
- [x] Plan 3: Pipeline Integration & Configurable Compression Modes

### Phase 12: improve citation detection

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 11
**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd-plan-phase 12 to break down)

---

## Phase 11: Improve the frontend UI

**Goal:** Improve the frontend UI layout, interactive dashboard widgets, styling, and user experience of ResearchSense based on the specifications.
**Depends on:** Phase 8 (Web Frontend Dashboard), Phase 10 (Pipeline integration and optimizations)

**Requirements Mapped:**

- UI-01: Redesign the UI dashboard widgets for an interactive and premium experience
- UI-02: Enhance the styling with rich glassmorphism, responsive grids, and micro-animations
- UI-03: Improve the layout hierarchy to prioritize key metrics like overall score and grade

**Success Criteria:**

1. Dashboard layout updated with rich glassmorphism styling and responsive grid elements
2. Frontend dashboard displays verified/unverified citation summaries and detailed reference entries cleanly
3. Interactive dashboard charts or gauges show the grade and status labels appropriately

**Plans:** 1 plans

Plans:

- [/] Plan 1: Design and implement UI/UX improvements for the frontend dashboard
