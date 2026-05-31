# ResearchSense — PPT Content Document
**AI-Based Academic Paper Analysis and Error Detection System**  
*Prepared: April 2026 | Mini Project Presentation*

---
---

## 1. Project Title Justification

### Slide Title: Why "ResearchSense"?

### Slide Content:

**Full Title:** ResearchSense — AI-Based Academic Paper Analysis and Error Detection System

**Name Breakdown:**
- **"Research"** — Directly references the domain: academic research papers, the core input of the system.
- **"Sense"** — Carries a dual meaning:
  1. **Making sense of** — The system interprets and evaluates complex academic writing, transforming unstructured PDF content into structured, actionable feedback.
  2. **Sensibility/judgement** — Reflects the system's ability to apply intelligent, multi-dimensional judgement to assess paper quality — similar to what a human reviewer does, but automated and instant.

**Why This Name Works:**
- It is concise, memorable, and immediately communicates purpose.
- It positions the tool as an intelligent companion for researchers — not just a grammar checker, but a comprehensive quality evaluator.
- The name avoids technical jargon, making it accessible to all audiences (students, professors, evaluators).

**Alternative Titles Considered:**
| Rejected Title | Reason for Rejection |
|---|---|
| PaperGrader | Too narrow — implies only grading, not analysis |
| AI Paper Reviewer | Too generic — doesn't distinguish from existing tools |
| ResearchLint | Too developer-centric — won't resonate with academic audience |
| AcademicSense | Less specific — could apply to any academic tool |

> **💬 Speaker Note:** "We chose 'ResearchSense' because it captures both what the system does — making sense of research papers — and how it does it — with AI-driven sensibility. It's a name that a student can immediately understand without needing a technical background."

---
---

## 2. Objective and Scope of the Project

### Slide Title: Objective & Scope

### Target Users:
- University students submitting research papers
- Researchers preparing journal submissions
- Academics who want pre-review quality checks

### Primary Objective:

To design and develop an AI-powered web application that automatically analyzes the quality of academic research papers across **8 evaluation dimensions** and generates a **structured feedback report with a confidence score (0–100)** — enabling students and researchers to identify and fix weaknesses in their papers before formal submission.

### Specific Objectives:

1. **Automate Multi-Dimensional Quality Assessment** — Build a pipeline that evaluates grammar, readability, abstract quality, structural integrity, methodology soundness, logical consistency, conclusion completeness, and citation credibility — all in a single upload.

2. **Leverage AI for Deep Textual Analysis** — Use Google's Gemini 2.5 Flash (Large Language Model) to perform nuanced, context-aware evaluation that goes beyond surface-level spell-checking.

3. **Verify Citation Authenticity** — Cross-reference citations against Semantic Scholar's database of 200M+ papers and validate DOIs through CrossRef's official registry.

4. **Produce Actionable Output** — Generate a downloadable PDF report with per-dimension scores, specific issues found, and concrete improvement suggestions.

5. **Provide Instant Feedback** — Reduce the feedback loop from weeks (traditional peer review) to under 60 seconds.

### Scope:

**In Scope (What the system WILL do):**

| Feature | Description |
|---------|-------------|
| PDF Upload & Parsing | Accept PDF research papers and extract text using PyMuPDF |
| Section Detection | Automatically identify standard academic sections (Abstract, Introduction, Methodology, Results, Conclusion, References) |
| 8-Layer AI Analysis | Evaluate paper quality across 8 research-backed dimensions |
| Weighted Scoring | Calculate a composite confidence score (0–100) with letter grade (A–F) |
| PDF Report Generation | Produce a structured, downloadable analysis report |
| Web Interface | Provide a drag-and-drop upload UI with real-time results display |
| Citation Verification | Validate references against Semantic Scholar and CrossRef databases |

**Out of Scope (What the system will NOT do):**

| Feature | Reason |
|---------|--------|
| Plagiarism Detection | Separate domain — tools like Turnitin already cover this |
| User Accounts/Login | Not required for v1; simplifies the experience |
| Paper Storage/History | Privacy-first — papers are analyzed and immediately discarded |
| Mobile Application | Web-first approach is sufficient for university demonstration |
| Real-time Collaboration | System is designed for single-user, single-paper analysis |

> **💬 Speaker Note:** "The key differentiator of ResearchSense is that it doesn't just check grammar like Grammarly. It evaluates 8 separate quality dimensions — the same criteria that real peer reviewers use. A student uploads their paper and gets back a full quality assessment in under a minute, compared to weeks or months of waiting for traditional peer review feedback."

> **💬 Additional Description:** The scope is deliberately focused on delivering maximum value with minimum complexity. By excluding features like user accounts and paper storage, we keep the system lightweight, privacy-respecting, and easy to demo. The 8 evaluation dimensions are drawn from peer review standards used at top-tier CS conferences (ACM, IEEE, etc.) — specifically a four-dimensional framework covering technical content, structural coherence, writing precision, and ethical integrity.

---
---

## 3. Basic Concepts Related to the Project

### Slide Title: Key Concepts & Technologies

### 3.0 System Architecture (Overview Diagram)

This diagram shows the complete end-to-end pipeline — use it as a visual slide:

**Core Flow (Simplified):**
```
User uploads PDF
      ↓
Text Extraction (PyMuPDF)
      ↓
Section Splitting (Rule-based Python regex)
      ↓
8-Layer Analysis (Gemini API + Semantic Scholar + CrossRef)
      ↓
Scoring Algorithm (Custom Python — weighted average)
      ↓
Report Generation (ReportLab PDF)
      ↓
Display in Web UI
```

**Full Pipeline Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (HTML/CSS/JS)               │
│              Upload Form + Report Display UI             │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP POST (PDF file)
┌──────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI)                       │
│   /analyze endpoint → orchestrates entire pipeline       │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────────┐
│  PDF PARSER     │  ← PyMuPDF (local)
│  Text Extractor │
└──────┬──────────┘
       │
┌──────▼──────────┐
│ SECTION SPLITTER│  ← Rule-based Python regex
│ Abstract / Intro│
│ Method / Results│
│ Conclusion / Ref│
└──────┬──────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│                    ANALYSIS LAYERS                        │
│                                                           │
│  Layer 1: Grammar & Language       → Gemini API          │
│  Layer 2: Readability Score        → Gemini API          │
│  Layer 3: Abstract Quality         → Gemini API          │
│  Layer 4: Structural Integrity     → Gemini API          │
│  Layer 5: Methodology Soundness    → Gemini API          │
│  Layer 6: Logical Consistency      → Gemini API          │
│  Layer 7: Conclusion Completeness  → Gemini API          │
│  Layer 8: Citation Quality         → Semantic Scholar    │
│                                    + CrossRef API        │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────────┐
│ SCORING ENGINE  │  ← Custom Python (weighted average)
│ Confidence Score│
└──────┬──────────┘
       │
┌──────▼──────────┐
│ REPORT GENERATOR│  ← ReportLab (PDF output)
│ Structured PDF  │
└─────────────────┘
```

> **💬 Speaker Note:** "This is the full pipeline. A single PDF goes in at the top, passes through 6 stages, and comes out as a scored report at the bottom. Every box maps to a specific Python module in our codebase."

### 3.1 Natural Language Processing (NLP)

NLP is a branch of Artificial Intelligence that enables computers to understand, interpret, and generate human language. In ResearchSense, NLP powers the core analysis — the system reads academic text and evaluates its quality just as a human reviewer would.

**How NLP is used in this project:**
- Analyzing grammar, sentence clarity, and writing tone
- Evaluating whether an abstract contains all required elements
- Checking logical consistency between sections of a paper
- Assessing readability level and vocabulary complexity

### 3.2 Large Language Models (LLMs)

LLMs are AI models trained on massive datasets of text. They can understand context, generate responses, and perform complex reasoning tasks. ResearchSense uses **Google Gemini 2.5 Flash** — a state-of-the-art LLM with a 1 million token context window, meaning it can process an entire research paper in a single API call.

**Why Gemini 2.5 Flash?**
- Free tier available (250 requests/day, 10 requests/minute)
- 1 million token context window — can handle full-length papers
- Strong at generating structured JSON output — ideal for automated scoring
- Fast response time (Flash variant optimized for speed)

### 3.3 PDF Parsing & Text Extraction

Research papers are distributed as PDFs, which are not directly readable by AI systems. **PyMuPDF** (also called `fitz`) is a Python library that extracts text from PDF files, handling:
- Multi-column academic layouts
- Embedded fonts and special characters
- OCR (Optical Character Recognition) for scanned documents via Tesseract integration

**pymupdf4llm** is an extension that converts PDFs to Markdown format, which preserves heading structure — critical for detecting sections like "Abstract", "Methodology", etc.

### 3.4 API Integration (Application Programming Interface)

APIs allow different software systems to communicate. ResearchSense integrates with 3 external APIs:

| API | Purpose | Data |
|-----|---------|------|
| **Google Gemini API** | AI-powered text analysis | Evaluates 7 quality dimensions |
| **Semantic Scholar API** | Citation verification | Searches 200M+ academic papers |
| **CrossRef API** | DOI validation | Official DOI registry for publications |

### 3.5 What Each Layer Specifically Checks

The 8 evaluation parameters are drawn from peer review standards at **11 top-tier CS conferences** and a four-dimensional framework (technical content, structural coherence, writing precision, ethical integrity).

| # | Layer | Weight | What It Checks |
|---|-------|--------|----------------|
| 1 | Grammar & Language | 15% | Spelling/grammar errors, sentence clarity, passive voice overuse, academic tone, word choice |
| 2 | Readability Score | 10% | Sentence length/complexity, jargon density, Flesch Reading Ease, audience accessibility |
| 3 | Abstract Quality | 10% | Presence of problem/methodology/results/conclusion, standalone readability, word count (150–300) |
| 4 | Structural Integrity | 15% | Required sections present, correct order, Keywords section, heading formatting |
| 5 | Methodology Soundness | 15% | Research design clarity, tools/datasets justified, sample size explained, limitations acknowledged, reproducibility |
| 6 | Logical Consistency | 15% | Results prove Abstract claims, Methods→Results alignment, Conclusion reflects Results, no contradictions |
| 7 | Conclusion Completeness | 10% | Answers research question, summarizes findings, discusses implications, mentions limitations, suggests future work |
| 8 | Citation Quality | 10% | Citations exist (Semantic Scholar), DOIs valid (CrossRef), formatting correct, no self-citation abuse, recency |

### 3.6 Weighted Scoring Algorithm

A mathematical method to calculate a composite quality score from multiple individual metrics, where each metric contributes differently based on its importance.

**Formula:**
```
Confidence Score = Σ (Layer Score × Weight) × 10
```
Where each Layer Score is 0–10, producing a final score of 0–100.

**Example Scoring Run (from a real paper):**
```
Grammar:       8/10 × 15% = 12.0
Readability:   7/10 × 10% =  7.0
Abstract:      9/10 × 10% =  9.0
Structure:     8/10 × 15% = 12.0
Methodology:   6/10 × 15% =  9.0
Logic:         7/10 × 15% = 10.5
Conclusion:    8/10 × 10% =  8.0
Citations:     9/10 × 10% =  9.0
────────────────────────────────
Weighted sum:              76.5
Final Score:   76.5 / 100  →  Grade: B — Good
```

**Grading Scale:**

| Score Range | Grade | Meaning |
|-------------|-------|---------|
| 85–100 | A | Excellent — ready for submission |
| 70–84 | B | Good — minor improvements needed |
| 55–69 | C | Needs Improvement — significant revisions required |
| 40–54 | D | Poor — major structural/quality issues |
| 0–39 | F | Very Poor — fundamental rework needed |

> **💬 Speaker Note:** "Notice in the example — this paper scored well in grammar and citations but only 6/10 in methodology. That's exactly the kind of targeted feedback ResearchSense provides. The student now knows exactly where to focus their revision effort. With 250 requests/day on the free tier, we can analyze approximately 30 full papers per day — more than enough for a university setting."

### 3.7 RESTful Web Services (FastAPI)

**FastAPI** is a modern Python web framework used to build the backend server. It:
- Receives PDF uploads from the frontend
- Orchestrates the full analysis pipeline
- Returns results as JSON data
- Auto-generates interactive API documentation at `/docs`

### 3.8 Report Generation (ReportLab)

**ReportLab** is a Python library for creating professional PDF documents programmatically. It generates the final analysis report containing:
- Overall confidence score and letter grade
- Per-dimension score breakdown
- Specific issues found in each layer
- Actionable improvement suggestions

> **💬 Speaker Note:** "These are not just theoretical concepts — each one directly maps to a component in our system. NLP and LLMs power the analysis, PyMuPDF handles the input, APIs provide external validation, the weighted algorithm produces the score, FastAPI serves it all, and ReportLab creates the output. Together, they form an end-to-end pipeline from PDF upload to quality report."

> **💬 Additional Description:** The choice of these specific technologies was driven by three constraints: (1) everything must be free-tier, (2) everything must be Python-based for consistency, and (3) everything must be reliable enough for a live demo. Gemini's free tier gives us 250 calls/day — more than enough for ~30 paper analyses per day. Semantic Scholar covers 200M+ papers across all academic disciplines. CrossRef is the official DOI registry used by every major publisher worldwide.

---
---

## 4. Analysis and Explanation of the Identified Problem

### Slide Title: The Problem We're Solving

### 4.1 The Problem

**Academic research paper quality is declining, and students have no way to get instant, comprehensive feedback before submission.**

The current academic publishing ecosystem faces a compounding crisis:

**For Students & Early-Career Researchers:**
- First-time researchers struggle with academic writing standards — common issues include poor paper structure, unclear methodology descriptions, grammatical errors, and inadequate citations.
- Students often don't know if their paper meets publication standards until it's too late — peer review feedback takes weeks to months.
- 30–70% of all manuscripts are "desk rejected" — rejected by editors without even reaching peer review — primarily due to structural and writing quality issues that could have been caught early.
- Non-native English speakers are disproportionately disadvantaged by language bias in the review process.

**For the Academic Ecosystem:**
- Top-tier journals like *Nature* and *Science* have acceptance rates below 8%.
- The peer review system is in crisis — reviewer invitation acceptance rates dropped from 56% (2020) to ~36% (2024–2025), creating massive delays.
- The time from submission to first decision has extended beyond a year at some journals.
- Over 26% of scientific abstracts are now written beyond college-graduate reading level, making them inaccessible even within the academic community.

### 4.2 Why Existing Tools Fall Short

| Tool/Approach | What It Does | What It Misses |
|--------------|--------------|----------------|
| **Grammarly** | Grammar, spelling, tone | No methodology analysis, no citation verification, no structural evaluation, no academic-specific scoring |
| **Turnitin** | Plagiarism detection | Does not evaluate quality, structure, or scientific rigor |
| **Manual Peer Review** | Comprehensive evaluation | Takes weeks/months, overloaded reviewers, inconsistent quality, not accessible pre-submission |
| **University Writing Centers** | General writing feedback | Not scalable, limited availability, no domain-specific academic paper expertise at scale |
| **ChatGPT / Generic AI** | Can answer questions about a paper | No structured evaluation framework, no citation verification, no standardized scoring, no downloadable report |

**The Gap:** No existing tool provides a **structured, multi-dimensional, automated quality assessment** of research papers with **citation verification** and a **standardized confidence score** — all in under 60 seconds.

### 4.3 Who Is Affected?

| User Group | Pain Point | How ResearchSense Helps |
|-----------|------------|------------------------|
| University students | "Is my paper good enough to submit?" | Instant 8-dimension quality assessment with letter grade |
| First-time researchers | "I don't know what peer reviewers look for" | Evaluates the exact criteria reviewers use |
| Non-native English speakers | "My ideas are good but my writing gets rejected" | Identifies specific grammar/clarity issues with corrections |
| Research supervisors | "I review the same mistakes in every student's draft" | Students self-check before submitting to supervisor |

### 4.4 The Scale of the Problem

- **~5 million** research papers are published annually worldwide (and growing ~5% per year)
- **30–70%** desk rejection rate at most journals
- **Top reasons for rejection:** Poor writing quality, weak methodology, missing structural elements — all things ResearchSense checks
- **Average peer review time:** 3–6 months — ResearchSense does it in under 60 seconds

> **💬 Speaker Note:** "The core insight is this: most papers don't get rejected because the research is bad — they get rejected because the writing, structure, or presentation doesn't meet the standard. These are fixable problems. ResearchSense catches them before the student even hits 'submit.' Think of it as a pre-flight checklist for research papers."

> **💬 Additional Description:** This is not about replacing peer review — peer reviewers evaluate scientific novelty and contribution, which requires deep domain expertise. ResearchSense handles the quality dimensions that don't need domain expertise: Is the grammar correct? Is the structure sound? Are the citations real? Does the conclusion match the results? By catching these issues early, we free up peer reviewers to focus on what actually matters — evaluating the science itself.

---
---

## 5. Software and Hardware Requirements

### Slide Title: System Requirements

### 5.1 Software Requirements

#### Development Environment

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10+ | Primary programming language |
| pip | Latest | Package manager for Python dependencies |
| Git | Latest | Version control |
| VS Code / Any IDE | Latest | Code editor |
| Web Browser | Chrome/Edge/Firefox | Frontend testing and API documentation |

#### Backend Dependencies (Python Packages)

| Package | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115.x | Web framework for REST API |
| Uvicorn | Latest | ASGI server to run FastAPI |
| python-multipart | Latest | File upload handling |
| google-generativeai | Latest | Google Gemini API SDK |
| PyMuPDF (fitz) | 1.27.x | PDF text extraction |
| pymupdf4llm | Latest | Enhanced PDF-to-Markdown for LLM pipelines |
| semanticscholar | 0.12.x | Semantic Scholar API client |
| requests | Latest | HTTP client for CrossRef API |
| ReportLab | 4.x | PDF report generation |
| python-dotenv | Latest | Environment variable management |

#### Frontend Technologies

| Technology | Purpose |
|------------|---------|
| HTML5 | Page structure and semantic markup |
| CSS3 | Styling, responsive layout, animations |
| JavaScript (ES6+) | API communication, drag-and-drop, DOM manipulation |

#### External APIs (All Free Tier)

| API | Provider | Free Tier Limits | Purpose |
|-----|----------|-------------------|---------|
| Gemini 2.5 Flash | Google | 250 RPD, 10 RPM, 250K TPM | AI-powered 7-layer text analysis |
| Semantic Scholar | Allen Institute for AI | 1 RPS (public), 10 RPS (with key) | Citation verification (200M+ papers) |
| CrossRef REST API | CrossRef | No formal limit (polite pool) | DOI validation and metadata retrieval |

#### Operating System

| OS | Support |
|----|---------|
| Windows 10/11 | ✅ Fully supported (primary development) |
| macOS | ✅ Fully supported |
| Linux (Ubuntu 20.04+) | ✅ Fully supported |

### 5.2 Hardware Requirements

#### Minimum Requirements (Development & Demo)

| Component | Specification | Justification |
|-----------|---------------|---------------|
| Processor | Intel i3 / AMD Ryzen 3 (or equivalent) | FastAPI and Python processing are lightweight |
| RAM | 4 GB | Sufficient for running backend + browser |
| Storage | 500 MB free space | For Python packages, project files, and temporary PDFs |
| Internet | Stable broadband connection | Required for Gemini API, Semantic Scholar, and CrossRef calls |

#### Recommended Requirements (Smooth Experience)

| Component | Specification | Justification |
|-----------|---------------|---------------|
| Processor | Intel i5 / AMD Ryzen 5 (or better) | Faster PDF parsing and API response handling |
| RAM | 8 GB | Comfortable for development + testing |
| Storage | 1 GB free space | Extra space for logs, cached results, reports |
| Internet | 10+ Mbps | Faster API round-trips, especially for large papers |

#### Project File Structure

```
researchsense/
├── main.py              ← FastAPI app entry point
├── pdf_parser.py        ← PyMuPDF text extraction
├── section_detector.py  ← Section splitting logic
├── gemini_analyzer.py   ← All 7 Gemini API layers
├── citation_checker.py  ← Semantic Scholar + CrossRef
├── scoring.py           ← Confidence score algorithm
├── report_generator.py  ← ReportLab PDF generation
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── .env                 ← API keys (not committed to git)
└── requirements.txt     ← All Python dependencies
```

> **💬 Speaker Note:** "One of our key design decisions was that everything must be free. Every API, every library, every tool we use is open-source or has a free tier. A student with a basic laptop and an internet connection can run this entire system. There is zero cost — no cloud hosting required for the demo, no paid API keys, no premium subscriptions. The project is also cleanly modular — each Python file handles exactly one responsibility."

> **💬 Additional Description:** The system is designed to run entirely on localhost for the demo. The backend runs on `localhost:8000` via Uvicorn, and the frontend is served as static HTML files opened directly in the browser. No cloud deployment is needed for v1. The modular file structure means each component can be developed and tested independently — `pdf_parser.py` can be tested without Gemini, `scoring.py` can be tested with mock data, etc.

---
---

## 6. Plan of Action

### Slide Title: Implementation Plan & Timeline

### 6.1 Development Methodology

We follow an **incremental build-and-test** approach — each phase builds on the previous one, is independently testable, and delivers visible progress.

### 6.2 Phase Breakdown

#### Phase 1: Environment Setup & PDF Parser (Week 1–2)

**Goal:** Set up the project foundation and implement PDF text extraction with section detection.

| Task | Deliverable |
|------|-------------|
| Set up Python virtual environment and install all dependencies | `requirements.txt` with all packages |
| Configure API keys (Gemini, Semantic Scholar) in `.env` | Working API authentication |
| Build FastAPI skeleton with `/analyze` endpoint | Server running on `localhost:8000` |
| Implement PDF text extraction using PyMuPDF/pymupdf4llm | Raw text extracted from any uploaded PDF |
| Implement section detection (regex-based + Gemini AI fallback) | Paper split into: Abstract, Introduction, Methodology, Results, Conclusion, References |
| Test with 3–5 real research papers | Verified extraction accuracy |

**Milestone:** Upload a PDF → get back a JSON response with detected sections.

---

#### Phase 2: AI Analysis Engine (Week 2–4)

**Goal:** Implement all 7 Gemini-powered evaluation layers.

| Task | Deliverable |
|------|-------------|
| Build Gemini API integration with authentication | Working API connection |
| Implement Layer 1: Grammar & Language analysis | JSON output with errors, corrections, severity |
| Implement Layer 2: Readability Score | Readability score + complexity assessment |
| Implement Layer 3: Abstract Quality | Element-by-element abstract evaluation |
| Implement Layer 4: Structural Integrity | Section presence/order validation |
| Implement Layer 5: Methodology Soundness | Research design evaluation |
| Implement Layer 6: Logical Consistency | Cross-section contradiction detection |
| Implement Layer 7: Conclusion Completeness | Conclusion element checklist |
| Implement rate limit handling (exponential backoff) | Reliable API calls even under load |
| Implement JSON response validation and error handling | Graceful degradation on malformed API responses |

**Milestone:** Upload a PDF → get back 7 independent layer evaluations in JSON format.

---

#### Phase 3: Citation Verification & Scoring (Week 4–5)

**Goal:** Complete Layer 8 (citations) and compute the final confidence score.

| Task | Deliverable |
|------|-------------|
| Extract citations/references from the References section | List of reference titles and DOIs |
| Implement Semantic Scholar citation verification | Verified/unverified status for each reference |
| Implement CrossRef DOI validation | DOI validity check with metadata retrieval |
| Implement citation quality scoring algorithm | Citation credibility score (0–10) |
| Implement weighted scoring algorithm (all 8 layers) | Final confidence score (0–100) and letter grade (A–F) |
| Test scoring with diverse papers (good, mediocre, poor) | Calibrated scoring that matches human judgment |

**Milestone:** Full pipeline works end-to-end — upload PDF → get a confidence score with all 8 layers evaluated.

---

#### Phase 4: Report Generation & Web UI (Week 5–6)

**Goal:** Build the final user-facing outputs — PDF report and web interface.

| Task | Deliverable |
|------|-------------|
| Design and build ReportLab PDF report template | Professional PDF with score breakdown, findings, and suggestions |
| Implement report download endpoint in FastAPI | `/report` endpoint returns downloadable PDF |
| Build HTML/CSS frontend — upload page with drag-and-drop | Clean, responsive upload interface |
| Build results display page — score, grade, layer breakdown | Visual score presentation with per-layer details |
| Connect frontend to backend API | Full working integration |
| Pre-cache 5–10 sample paper results for demo backup | Reliable demo even if APIs are slow/down |
| End-to-end testing with diverse papers | System works reliably for live demo |

**Milestone:** Complete working application — upload a paper in the browser, see results on screen, download a PDF report.

---

### 6.3 Visual Timeline

```
Week 1 ──── Week 2 ──── Week 3 ──── Week 4 ──── Week 5 ──── Week 6
  │           │           │           │           │           │
  ├── Phase 1 ─┤           │           │           │           │
  │  Setup +   │           │           │           │           │
  │  PDF Parser│           │           │           │           │
  │            ├── Phase 2 ────────────┤           │           │
  │            │  AI Analysis Engine   │           │           │
  │            │  (7 Gemini Layers)    │           │           │
  │            │                       ├── Phase 3 ┤           │
  │            │                       │  Citations│           │
  │            │                       │  & Scoring│           │
  │            │                       │           ├── Phase 4 ┤
  │            │                       │           │  Reports  │
  │            │                       │           │  & Web UI │
  │            │                       │           │           │
                                                         DEMO DAY
```

### 6.4 Risk Mitigation Plan

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|--------|---------------------|
| Gemini free tier runs out (250 RPD) | Medium | High | Use Flash-Lite for simpler layers; cache results during testing |
| PDF with unusual format breaks parser | Medium | Medium | Gemini-based fallback section detection; test with diverse PDFs |
| Gemini returns invalid/unparseable JSON | Medium | Medium | Try/except with retry using stricter prompt; fallback to default scores |
| Semantic Scholar API downtime | Low | Low | 3-second timeout + retry; graceful degradation (skip citation check) |
| Rate limiting during live demo | Medium | High | Pre-cache 5–10 sample results; use a short (4-page) paper for live demo; have screenshots of full reports as backup |
| Scanned PDF with no extractable text | Medium | Low | OCR fallback via PyMuPDF's Tesseract integration |
| Paper has non-standard section names | Medium | Medium | Use Gemini as fallback section detector when regex fails |
| CrossRef API rate limiting | Low | Low | Add `mailto` parameter for polite pool; add 1-second delays between calls |

### 6.5 Testing Strategy

| Test Type | What We Test | When |
|-----------|-------------|------|
| Unit Testing | Individual functions (PDF extraction, scoring, section detection) | During each phase |
| Integration Testing | Full pipeline from PDF upload to report generation | After Phase 3 and Phase 4 |
| User Acceptance Testing | Real papers from actual students; compare scores to manual assessment | Week 5–6 |
| Demo Rehearsal | Simulate live demo conditions with pre-prepared papers | Week 6 (before demo day) |

> **💬 Speaker Note:** "Our biggest risk is Phase 2 — integrating 7 Gemini API layers with rate limiting. Our strategy is to get one layer working perfectly first, then use it as a template for the remaining six. If we hit a blocker, we can also combine multiple layers into fewer API calls by asking Gemini to evaluate several dimensions in a single prompt. The pre-cached demo results are our insurance policy — no matter what happens with the APIs on demo day, we can show a complete working result."

> **💬 Additional Description:** The 6-week timeline is compressed but achievable because (1) we have a comprehensive research document with exact code templates for every component, (2) the architecture is intentionally simple — no database, no auth, no deployment complexity, and (3) each phase has clear success criteria so we know exactly when to move on. The plan also builds in a "demo rehearsal" step in Week 6, which is critical for the external evaluation — we want to practice the exact flow we'll show the professor.

---
---

## Quick Reference: Slide-by-Slide Summary

| Slide # | Topic | Key Takeaway |
|---------|-------|-------------|
| 1 | Project Title Justification | "ResearchSense" = making sense of research + AI sensibility |
| 2 | Objective & Scope | 8-dimension automated quality analysis with confidence scoring |
| 3 | Basic Concepts | NLP, LLMs, PDF parsing, APIs, weighted scoring, FastAPI, ReportLab |
| 4 | Problem Analysis | 30–70% desk rejection rate; no tool offers comprehensive pre-submission checks |
| 5 | System Requirements | All free-tier; runs on any laptop with Python 3.10+ and internet |
| 6 | Plan of Action | 4 phases over 6 weeks; incremental build-and-test approach |

---

*Document prepared for ResearchSense Mini Project PPT*  
*April 2026*
