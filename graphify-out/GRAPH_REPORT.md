# Graph Report - mini project  (2026-06-02)

## Corpus Check
- 74 files · ~72,281 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1111 nodes · 1112 edges · 119 communities (89 shown, 30 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 20 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f27473dd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 107|Community 107]]
- [[_COMMUNITY_Community 108|Community 108]]
- [[_COMMUNITY_Community 109|Community 109]]
- [[_COMMUNITY_Community 110|Community 110]]
- [[_COMMUNITY_Community 111|Community 111]]
- [[_COMMUNITY_Community 112|Community 112]]
- [[_COMMUNITY_Community 113|Community 113]]
- [[_COMMUNITY_Community 114|Community 114]]
- [[_COMMUNITY_Community 115|Community 115]]
- [[_COMMUNITY_Community 116|Community 116]]
- [[_COMMUNITY_Community 117|Community 117]]
- [[_COMMUNITY_Community 118|Community 118]]

## God Nodes (most connected - your core abstractions)
1. `Conversation Log` - 42 edges
2. `ResearchSense — Complete Project Research Document` - 18 edges
3. `workflow` - 16 edges
4. `Antigravity ReportLab PDF — Skill Guide` - 16 edges
5. `Functions List` - 12 edges
6. `TestExtractDois` - 11 edges
7. `Functions List` - 11 edges
8. `3. Basic Concepts Related to the Project` - 11 edges
9. `Implementation Decisions` - 11 edges
10. `citations` - 10 edges

## Surprising Connections (you probably didn't know these)
- `_generate_verdict_paragraph()` --calls--> `_call_llm_with_failover()`  [INFERRED]
  MAIN_PROJECT/report_generator.py → MAIN_PROJECT/gemini_analyzer.py
- `Few-Shot Anchored Prompting` --semantically_similar_to--> `Score Clamping and Validation`  [INFERRED] [semantically similar]
  .planning/phases/07-output-consistency-and-overall-refinement/PLAN.md → .planning/phases/06-output-quality-optimization/PLAN.md
- `analyze_paper()` --calls--> `check_api_health()`  [INFERRED]
  MAIN_PROJECT/main.py → MAIN_PROJECT/gemini_analyzer.py
- `health_check()` --calls--> `check_api_health()`  [INFERRED]
  MAIN_PROJECT/main.py → MAIN_PROJECT/gemini_analyzer.py
- `PLAN.md (Ph6)` --conceptually_related_to--> `PLAN.md (Ph7)`  [INFERRED]
  .planning/phases/06-output-quality-optimization/PLAN.md → .planning/phases/07-output-consistency-and-overall-refinement/PLAN.md

## Hyperedges (group relationships)
- **Research Paper Analysis and Evaluation Flow** — main_analyze_paper, pdf_parser_extract_text, gemini_analyzer_analyze_paper, citation_checker_check_citations [EXTRACTED 0.95]
- **Failover-Safe LLM Interaction** — gemini_analyzer_call_llm_with_failover, gemini_analyzer_analyze_paper, report_generator_generate_verdict_paragraph [EXTRACTED 0.90]
- **Academic Analysis Pipeline Orchestration Flow** — run_local_run_pipeline, section_detector_detect_sections, scoring_calculate_score [EXTRACTED 0.95]
- **Active Project Milestone Planning Context** — planning_project_md, planning_roadmap_md, planning_state_md [EXTRACTED 0.98]
- **PDF Report Design and Retrieval Specification** — desirable_md, rationale_professor_facing_clinical_tone, explain_md [INFERRED 0.85]
- **Orchestrated Pipeline Flow** — main_py, pdf_parser_py, section_detector_py, gemini_analyzer_py, citation_checker_py, scoring_py, report_generator_py [EXTRACTED 0.95]
- **Phase Context Evolution** — 01_context_md, 02_context_md, 03_context_md, 04_context_md, 07_context_md [INFERRED 0.90]
- **PDF Layout and Theming System** — report_generator_py, pdf_skill_md, platypus_hybrid_architecture [EXTRACTED 0.95]

## Communities (119 total, 30 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (44): BytesIO, Flowable, _bar_color(), _build_citation_section(), _build_detected_sections(), _build_param_grid(), _build_story(), draw_cover() (+36 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (27): analyze_paper(), _call_gemini(), _call_llm_with_failover(), _call_single_key(), check_api_health(), clean_json_text(), _parse_retry_delay(), float (+19 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (39): agent_skills, brave_search, commit_docs, exa_search, features, firecrawl, git, branching_strategy (+31 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (23): check_citations, _verify_references_parallel, Few-Shot Anchored Prompting, analyze_paper, _call_llm_with_failover, Multi-Key API Rotation Pattern, FastAPI analyze_paper endpoint, FastAPI generate_report endpoint (+15 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (44): Assistant, Assistant, Assistant, Assistant, Assistant, Assistant, Assistant, Assistant (+36 more)

### Community 6 - "Community 6"
Cohesion: 0.16
Nodes (19): check_citations(), _detect_duplicates(), _extract_author_year_refs(), _extract_dois(), _extract_title_from_ref(), bool, int, str (+11 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (44): citations, flagged_dois, flagged_items, issues, not_found, score, suggestions, total_refs (+36 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (21): Agent's Discretion, API Design — Two endpoints, Canonical References, Deferred Ideas, Design Specification, Future Scope (not in MVP), Implementation Decisions, Integration Contract (+13 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (21): Antigravity ReportLab PDF — Skill Guide, Architecture Decision: PLATYPUS Hybrid (not pure Canvas), Checklist Before Running, Citation Analysis Section, Color Tokens, Common Errors & Fixes, Cover Page (`onPage` Canvas callback), Custom Flowables (+13 more)

### Community 10 - "Community 10"
Cohesion: 0.10
Nodes (20): Agent's Discretion, API Key & Configuration Management, Canonical References, Deferred Ideas, Error Handling & API Resilience, Established Patterns, Existing Code Insights, Future Scope (not in MVP) (+12 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (20): Agent's Discretion, Canonical References, citation_checker.py output shape, CrossRef Validation, Deferred Ideas, Design Spec, DOI Extraction, External API (+12 more)

### Community 13 - "Community 13"
Cohesion: 0.33
Nodes (8): _clean_heading(), detect_sections(), _is_heading_line(), bool, str, Strip markdown #, bold **, numbers, and whitespace to get pure heading text., Check if a line is a heading (markdown or short plain text)., Segment text (plain or markdown) into standard academic sections.      Works wit

### Community 16 - "Community 16"
Cohesion: 0.38
Nodes (6): bool, str, Saves content to base_name. If base_name is locked (PermissionError),     append, Run the entire ResearchSense pipeline on a local PDF file., run_pipeline(), save_file_safely()

### Community 17 - "Community 17"
Cohesion: 0.50
Nodes (3): extract_text(), str, Extract text from a PDF, with automatic fallback.      Primary:  PyMuPDF4LLM → s

### Community 21 - "Community 21"
Cohesion: 0.06
Nodes (30): 1. Grammar & Language &nbsp;&nbsp;&nbsp; `12 / 15`, 2. Structural Integrity &nbsp;&nbsp;&nbsp; `13 / 15`, 3. Methodology Soundness &nbsp;&nbsp;&nbsp; `10 / 15`, 4. Logical Consistency &nbsp;&nbsp;&nbsp; `12 / 15`, 5. Readability Score &nbsp;&nbsp;&nbsp; `8 / 10`, 6. Abstract Quality &nbsp;&nbsp;&nbsp; `8 / 10`, 7. Conclusion Completeness &nbsp;&nbsp;&nbsp; `7 / 10`, 8. Citation Quality &nbsp;&nbsp;&nbsp; `6 / 10` (+22 more)

### Community 23 - "Community 23"
Cohesion: 0.10
Nodes (19): 1. Project Overview, 2. Key Decisions Made, 3. Work Division, 4. Integration Plan, 5. Environment Setup (every team member), 6. Phase Timeline, 7. Demo Day Strategy, Core Flow (+11 more)

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (13): 13. Full Tech Stack Summary, 15. Project Timeline, 16. Risks & Mitigations, 2. System Architecture, 5. Section Detection, Fallback: Ask Gemini to Split Sections, Full Pipeline Architecture, One-Line Install (+5 more)

### Community 46 - "Community 46"
Cohesion: 0.05
Nodes (44): citations, flagged_dois, flagged_items, issues, not_found, score, suggestions, total_refs (+36 more)

### Community 48 - "Community 48"
Cohesion: 0.07
Nodes (29): Cleanup (lines 54–56), CORS middleware (lines 18–23), Creating the FastAPI app (line 15), Full file with explanation, Health check endpoint — `GET /` (lines 25–28), How to run it, Importing pipeline modules (lines 12–13), Imports (lines 1–6) (+21 more)

### Community 49 - "Community 49"
Cohesion: 0.33
Nodes (5): 1. Project Title Justification, Quick Reference: Slide-by-Slide Summary, ResearchSense — PPT Content Document, Slide Content:, Slide Title: Why "ResearchSense"?

### Community 52 - "Community 52"
Cohesion: 0.17
Nodes (11): Active, Constraints, Context, Core Value, Evolution, Key Decisions, Out of Scope, Requirements (+3 more)

### Community 53 - "Community 53"
Cohesion: 0.18
Nodes (10): AI Analysis Engine, Citations & Validation, Core Pipeline, (None currently deferred), Out of Scope, Requirements: ResearchSense, Scoring & Reporting, Traceability (+2 more)

### Community 54 - "Community 54"
Cohesion: 0.20
Nodes (9): Phase 1: Environment & PDF Parser, Phase 2: AI Analysis Engine, Phase 3: Citations & Scoring, Phase 4: Reporting & Web UI, Phase 5: Gemini 7-Layer AI Analysis Engine, Phase 6: Output Quality Optimization, Phase 7: Output Consistency and Overall Refinement, Phase 8: Web Frontend Dashboard (+1 more)

### Community 55 - "Community 55"
Cohesion: 0.22
Nodes (8): Accumulated Context, Interface Contract (Person 2 & 3 must consume this), Key Decisions (Plan 01), Progress, Project Reference, Project State, Report Design Decisions (desirable.md — 18 May 2026), Roadmap Evolution

### Community 61 - "Community 61"
Cohesion: 0.10
Nodes (19): 1.1.1 File Upload, 1.1.2 Pipeline Stage Tracker, 1.1 Upload & Pipeline View, 1.2.1 Overall Score & Grade, 1.2.2 Detected Sections Checklist, 1.2.3 Restructured Multi-Layer Review, 1.2.4 Citation & Reference Validator, 1.2.5 Overall Qualitative Verdict & Actions (+11 more)

### Community 62 - "Community 62"
Cohesion: 0.11
Nodes (18): 1.1 Color Palette (Harmonious Sleek Dark Mode), 1.2 Typography, 1.3 Micro-Animations & Dynamic States, 1. Design Aesthetics & Visual Identity, 2.1 File Upload & Pipeline Stage Tracker (Main View), 2.2.1 Hero Score Panel, 2.2.2 Detected Sections Pill-Grid, 2.2.3 Interactive Multi-Layer Analysis Grid (+10 more)

### Community 63 - "Community 63"
Cohesion: 0.11
Nodes (17): Agent's Discretion, Analysis Layers — Implementation, Canonical References, Citation Extraction (Layer 8 prep for Phase 3), Deferred Ideas, Existing Code Insights, Future Scope (not in MVP), Gemini API Setup (+9 more)

### Community 64 - "Community 64"
Cohesion: 0.12
Nodes (15): 1. Visual Identity & Architecture, 2. Upload Flow & Stage Stepper, 3. Analytics Dashboard & Interactive Panels, 4. PDF Integration & Pre-Flight Diagnostics, Backend Endpoints to Consume, Backend orchestrator `main.py` endpoints:, Canonical References, Deferred Ideas (+7 more)

### Community 65 - "Community 65"
Cohesion: 0.13
Nodes (14): 1. Scoring Consistency & LLM Settings, 2. Advanced Citation Title Checking, 3. Spacing, Formatting & PDF Polish, 4. API Pre-Flight & Diagnostics, Canonical References, Codebase Integration, Deferred Ideas, Existing Code Insights (+6 more)

### Community 66 - "Community 66"
Cohesion: 0.13
Nodes (14): Execution Order, Phase 7 — Output Consistency and Overall Refinement: PLAN, Plan 1: Deterministic Scoring & Few-Shot Prompting (OPT-01), Plan 2: Parallel Citation Title Verification (OPT-04), Plan 3: PDF Spacing, Formatting & Safe Keeping (OPT-03), Plan 4: API Pre-Flight & Health Checks (OPT-05), Tasks:, Tasks: (+6 more)

### Community 67 - "Community 67"
Cohesion: 0.23
Nodes (11): handleUploadedFile(), resetStepper(), resetUploadView(), runFakeStepperSequence(), runLivePaperAnalysis(), showToastNotification(), showView(), triggerDemoMode() (+3 more)

### Community 68 - "Community 68"
Cohesion: 0.14
Nodes (13): Accomplishments, Decisions Made, Dependency graph, Deviations from Plan, Files Created/Modified, Issues Encountered, Metrics, Next Phase Readiness (+5 more)

### Community 69 - "Community 69"
Cohesion: 0.14
Nodes (13): 3. Plan 3: Client JavaScript Orchestration & API Connectivity (`app.js`), Plan 1: Structural Scaffolding & Responsive Layout (HTML5), Plan 2: Professional Analytics Design System (CSS), Plan 4: PDF Downloading & Offline Mock Demo, Plan: Web Frontend Dashboard, Tasks, Tasks, Tasks (+5 more)

### Community 70 - "Community 70"
Cohesion: 0.15
Nodes (12): Must-Haves, Objective, Owner, Plan 01: Person 1 — Backend Core & PDF Pipeline, Processing Pipeline, Task 1: Project Scaffolding & Dependencies, Task 2: FastAPI Application Skeleton (main.py), Task 3: PDF Text Extraction (pdf_parser.py) (+4 more)

### Community 71 - "Community 71"
Cohesion: 0.18
Nodes (10): Must-Haves (derived from Phase 1 contribution), Objective, Owner, Plan 03: Person 3 — Citations, Report & Frontend Stubs, Task 1: Citation Checker Stub (citation_checker.py), Task 2: Report Generator Stub (report_generator.py), Task 3: Frontend UI — Upload Page (frontend/), Tasks (+2 more)

### Community 72 - "Community 72"
Cohesion: 0.18
Nodes (11): 3.0 System Architecture (Overview Diagram), 3.1 Natural Language Processing (NLP), 3.2 Large Language Models (LLMs), 3.3 PDF Parsing & Text Extraction, 3.4 API Integration (Application Programming Interface), 3.5 What Each Layer Specifically Checks, 3.6 Weighted Scoring Algorithm, 3.7 RESTful Web Services (FastAPI) (+3 more)

### Community 73 - "Community 73"
Cohesion: 0.20
Nodes (9): Canonical References (READ BEFORE STARTING), must_haves (goal-backward verification), Phase 2: AI Analysis Engine — Plan, Smoke test (run after all 3 tasks complete), Task 1 — Create `gemini_analyzer.py`, Task 2 — Create `scoring.py`, Task 3 — Wire into `main.py`, UAT criteria (manual — requires real Gemini API key) (+1 more)

### Community 74 - "Community 74"
Cohesion: 0.20
Nodes (9): Canonical References (READ BEFORE STARTING), must_haves (goal-backward verification), Phase 3: Citations & Scoring — Plan, Smoke tests (no network needed — run first), Task 1 — Create `citation_checker.py`, Task 2 — Wire `citation_checker` into `main.py`, Task 3 — Add `requests` to `requirements.txt`, UAT criteria (requires network — run after smoke tests pass) (+1 more)

### Community 75 - "Community 75"
Cohesion: 0.20
Nodes (9): Canonical References (READ BEFORE STARTING), Import and endpoint check, must_haves (goal-backward verification), Offline PDF test (no API key needed — skips Gemini verdict, uses fallback), Phase 4: Reporting — Plan, Task 1 — Create `report_generator.py`, Task 2 — Add `/report` endpoint to `main.py`, UAT criteria (requires running server + Gemini API key) (+1 more)

### Community 76 - "Community 76"
Cohesion: 0.22
Nodes (8): Must-Haves, Objective, Owner, Plan 02: Person 2 — Scoring Module, Task 1: Scoring Module (scoring.py), Tasks, Test Commands, Verification

### Community 77 - "Community 77"
Cohesion: 0.25
Nodes (7): 1. `report_generator.py` - Early SDK Client Initialization (Quality / Low), 2. `main.py` - Unvalidated `analysis` Dictionary (Quality / Low), 3. `report_generator.py` - Flowable Height Estimation (Quality / Low), Conclusion, Findings, Overview, Phase 04 Code Review

### Community 78 - "Community 78"
Cohesion: 0.25
Nodes (7): Analyze Any PDF, Environment Setup (first time only), Generate Test PDF (no API needed), Quick Start, ResearchSense — How to Run, Run Tests, Start API Server

### Community 79 - "Community 79"
Cohesion: 0.25
Nodes (8): 3. Gemini API — Core AI Engine, Basic Setup Code, Current Free Tier Limits (April 2026), Getting Your Free API Key, Handling Gemini API Rate Limits, Installation, Prompt Templates for Each Layer, Why Gemini?

### Community 81 - "Community 81"
Cohesion: 0.29
Nodes (7): 4. PDF Parsing — PyMuPDF, Advanced Extraction (Multi-column Academic Papers), Basic Text Extraction, Handling Scanned PDFs (OCR Fallback), Installation, Key Limitations to Know, Why PyMuPDF?

### Community 82 - "Community 82"
Cohesion: 0.29
Nodes (7): 7. Semantic Scholar API — Citation Check, Access & Limits, Citation Score Calculation, Installation, Usage — Batch Citation Verification, Usage — Search for a Paper, What It Does

### Community 84 - "Community 84"
Cohesion: 0.33
Nodes (6): 2. Objective and Scope of the Project, Primary Objective:, Scope:, Slide Title: Objective & Scope, Specific Objectives:, Target Users:

### Community 85 - "Community 85"
Cohesion: 0.33
Nodes (6): 4.1 The Problem, 4.2 Why Existing Tools Fall Short, 4.3 Who Is Affected?, 4.4 The Scale of the Problem, 4. Analysis and Explanation of the Identified Problem, Slide Title: The Problem We're Solving

### Community 86 - "Community 86"
Cohesion: 0.33
Nodes (6): 5.1 Software Requirements, Backend Dependencies (Python Packages), Development Environment, External APIs (All Free Tier), Frontend Technologies, Operating System

### Community 87 - "Community 87"
Cohesion: 0.33
Nodes (6): 5.2 Hardware Requirements, 5. Software and Hardware Requirements, Minimum Requirements (Development & Demo), Project File Structure, Recommended Requirements (Smooth Experience), Slide Title: System Requirements

### Community 88 - "Community 88"
Cohesion: 0.33
Nodes (6): 6.1 Development Methodology, 6.3 Visual Timeline, 6.4 Risk Mitigation Plan, 6.5 Testing Strategy, 6. Plan of Action, Slide Title: Implementation Plan & Timeline

### Community 89 - "Community 89"
Cohesion: 0.33
Nodes (6): 14. Installation & Setup Guide, Step 1 — Clone/Create Project, Step 2 — Install Dependencies, Step 3 — Environment Variables, Step 4 — Project Structure, Step 5 — Run the App

### Community 90 - "Community 90"
Cohesion: 0.33
Nodes (6): 8. CrossRef API — DOI Validation, Access & Limits, DOI Extraction from References, DOI Validation, Installation, What It Does

### Community 91 - "Community 91"
Cohesion: 0.40
Nodes (5): 6.2 Phase Breakdown, Phase 1: Environment Setup & PDF Parser (Week 1–2), Phase 2: AI Analysis Engine (Week 2–4), Phase 3: Citation Verification & Scoring (Week 4–5), Phase 4: Report Generation & Web UI (Week 5–6)

### Community 92 - "Community 92"
Cohesion: 0.40
Nodes (5): 10. Backend — FastAPI, Core API Structure, Installation, Running the Server, Why FastAPI?

### Community 93 - "Community 93"
Cohesion: 0.40
Nodes (5): 11. Frontend, API Call (app.js), Minimal Frontend Structure, Recommended: Simple HTML + CSS + JavaScript, Upload Form (index.html core)

### Community 94 - "Community 94"
Cohesion: 0.50
Nodes (4): 1. Project Overview, Core Flow, Target Users, What is ResearchSense?

### Community 95 - "Community 95"
Cohesion: 0.67
Nodes (3): 12. Report Generation — ReportLab, Generate PDF Report, Installation

### Community 96 - "Community 96"
Cohesion: 0.67
Nodes (3): 6. Evaluation Parameters (8 Layers), Parameter Weights, What Each Parameter Checks

### Community 97 - "Community 97"
Cohesion: 0.67
Nodes (3): 9. Scoring Algorithm, Example Scoring Run, Weighted Average Formula

### Community 107 - "Community 107"
Cohesion: 0.33
Nodes (5): Artifacts & Code Modifications, Created Files, Summary: Web Frontend Dashboard, Verification & Telemetry Results, What Was Achieved

### Community 111 - "Community 111"
Cohesion: 0.10
Nodes (20): 1. System Architecture & Dev Setup, 2. Interactive Application State Flow, 3.1 Pre-Flight Diagnostics (`GET /health`), 3.2 Paper Analysis Upload (`POST /analyze`), 3.3 Dynamic Report PDF Compiler (`POST /report`), 3. Backend REST API Endpoints Specification, 4.1 High-Fidelity Drag-and-Drop Dropzone, 4.2 Dynamic Multi-Stage Processing Stepper (+12 more)

### Community 112 - "Community 112"
Cohesion: 0.09
Nodes (21): 1.1 Complete System Architecture Flow, 1. Global Pipeline Architecture & Orchestration, 3.1 Styling Engine: `style.css`, 3.2 Client Orchestration: `app.js`, 3. Frontend Component Blueprint & Reference, 4. Summary Matrix: Component Mapping, `checkBackendHealth()`, Core Design System Tokens (`:root`) (+13 more)

### Community 113 - "Community 113"
Cohesion: 0.17
Nodes (12): Custom Flowable: `ProgressBar`, Custom Flowable: `ScoreHero`, Custom Flowable: `SectionHeader`, Custom Flowable: `VerdictCard`, `draw_cover(canvas, doc)`, `draw_footer(canvas, doc)`, Functions List, `generate_pdf_report(...)` (+4 more)

### Community 114 - "Community 114"
Cohesion: 0.20
Nodes (10): 2.2 Document Extraction: `pdf_parser.py`, 2.4 Generative AI Layer: `gemini_analyzer.py`, 2.5 Bibliography Engine: `citation_checker.py`, 2.6 Weighted Scorer: `scoring.py`, 2.7 PDF Generator: `report_generator.py`, 2. Backend Component Blueprint & Reference, `calculate_score(layer_scores)`, `extract_text(pdf_path)` (+2 more)

### Community 115 - "Community 115"
Cohesion: 0.22
Nodes (9): `check_citations(references_text, full_text)`, `_detect_duplicates(references_text)`, `_extract_author_year_refs(text)`, `_extract_dois(references_text)`, `_extract_title_from_ref(ref_line)`, Functions List, `_validate_doi(doi)`, `_verify_references_parallel(ref_lines)` (+1 more)

### Community 116 - "Community 116"
Cohesion: 0.25
Nodes (8): `analyze_paper(sections)`, `_call_gemini(prompt)`, `_call_llm_with_failover(prompt)`, `_call_single_key(key_name, client, prompt)`, `check_api_health()`, `clean_json_text(text)`, Functions List, `_parse_retry_delay(err_str)`

### Community 117 - "Community 117"
Cohesion: 0.33
Nodes (6): 2.1 API Orchestrator: `main.py`, `analyze_paper(file)`, Functions List, `generate_report(analysis)`, `health_check()`, `root()`

### Community 118 - "Community 118"
Cohesion: 0.40
Nodes (5): 2.3 Academic Segmenter: `section_detector.py`, `_clean_heading(line)`, `detect_sections(text)`, Functions List, `_is_heading_line(line)`

## Knowledge Gaps
- **632 isolated node(s):** `final_score`, `grade`, `Abstract`, `Introduction`, `Related Work` (+627 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_generate_verdict_paragraph()` connect `Community 0` to `Community 1`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `_call_llm_with_failover()` connect `Community 1` to `Community 0`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `2. Backend Component Blueprint & Reference` connect `Community 114` to `Community 112`, `Community 117`, `Community 118`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **What connects `final_score`, `grade`, `Abstract` to the rest of the system?**
  _690 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05388471177944862 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.09852216748768473 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._