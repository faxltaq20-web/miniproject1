# ResearchSense — Team Summary & Work Division
**AI-Based Academic Paper Analysis and Error Detection System**
*Prepared: April 2026 | Mini Project | Team of 3*

---

## 1. Project Overview

**ResearchSense** is an AI-powered web application where professors and students upload a research paper PDF and receive a structured quality analysis report with a confidence score (0–100) and letter grade (A–F).

### Core Flow
```
User uploads PDF
      ↑
Text Extraction (PyMuPDF basic get_text())
      ↓
Section Detection (Regex-only)
      ↓
8-Layer Analysis (Gemini API × 7 layers + Citation APIs × 1 layer)
      ↓
Weighted Scoring Algorithm (custom Python)
      ↓
PDF Report Generation (ReportLab)
      ↓
Display in Web UI
```

### Primary Users
- **Professors** (primary) — use the report as a formal review instrument to assess if a student's paper is ready for journal/conference submission
- **Students** (secondary) — self-check their paper before submitting to their professor

### Tech Stack (all free)
| Component | Technology |
|-----------|-----------|
| AI Engine | Google Gemini 2.5 Flash (primary) + Flash-Lite (fallback) |
| PDF Parsing | PyMuPDF (`get_text()`) — simple text extraction |
| Citation Check | Semantic Scholar API + CrossRef API |
| Backend | FastAPI + Uvicorn |
| Report | ReportLab |
| Frontend | HTML + CSS + JavaScript |

---

## 2. Key Decisions Made

| Decision | Choice | Reason |
|----------|--------|--------|
| PDF extraction | Basic `get_text()` via PyMuPDF | Simple, reliable, no extra dependencies |
| pymupdf4llm | Not used — future scope | Unnecessary complexity for MVP |
| Scanned PDFs | Simple error, text-based PDFs only | MVP scope; OCR is future |
| Section detection | Regex-only, no Gemini fallback | No API quota wasted on section parsing |
| Missing sections | Soft warning, analysis proceeds | No strict rejection gate for MVP |
| Project layout | Modular from day 1 | Clean team ownership per file |
| API keys | `.env` file with python-dotenv | Easy to change keys/models, safe for GitHub |
| API failure | Single model (Flash), fail fast with clear error | No multi-model orchestration in MVP |
| Invalid JSON from Gemini | Retry once with stricter prompt → 0/10 | Graceful degradation |
| Team collaboration | GitHub branches per module | Clean integration, no conflicts |
| Primary audience | Professors (not students) | Report tone is formal/clinical |
| Report tone | Peer-review style, not coaching | Formal language throughout |

---

## 3. Work Division

The project is split into **3 module groups** — one per team member. Each person owns their files end-to-end: write, test, and hand off to GitHub.

---

### 👤 Person 1 — Backend Core & PDF Pipeline

**Files owned:**
```
main.py              ← FastAPI app, /analyze endpoint, orchestration
pdf_parser.py        ← basic PyMuPDF get_text() extraction
section_detector.py  ← regex-only section detection (no Gemini fallback)
.env.example         ← template for environment variables (no real keys)
requirements.txt     ← all Python dependencies
```

**Responsibilities:**
- Set up the Python virtual environment and install all dependencies
- Build the FastAPI skeleton with the `/analyze` endpoint
- Implement PDF text extraction using **basic PyMuPDF `get_text()`** (no pymupdf4llm)
- Implement **regex-only** section detection (patterns from ResearchSense_Research.md §5) — no Gemini fallback
- If a PDF yields no extractable text: return a simple error message (no OCR, no Tesseract)
- If sections are missing: populate those keys as empty strings `""` and add a soft warning in the response — **do not block analysis**
- Wire up `.env` loading with python-dotenv
- Add CORS middleware so the frontend can call the backend

**Deliverable (end of Phase 1):**
- POST a PDF to `http://localhost:8000/analyze` → get back JSON with detected sections:
```json
{
  "sections": {
    "abstract": "...",
    "introduction": "...",
    "methodology": "...",
    "results": "...",
    "conclusion": "...",
    "references": "..."
  }
}
```

**Key reference sections in ResearchSense_Research.md:**
- §4 — PyMuPDF extraction code (use basic `get_text()` only)
- §5 — Section detection regex patterns (regex only, skip Gemini fallback section)
- §10 — FastAPI skeleton
- §14 — Setup guide and project structure

---

### 👤 Person 2 — AI Analysis Engine & Scoring

**Files owned:**
```
gemini_analyzer.py   ← all 7 Gemini analysis layers
scoring.py           ← weighted confidence score algorithm
```

**Responsibilities:**
- Integrate Google Gemini API (`google-generativeai` SDK) with **single model** (`gemini-2.5-flash`) — no multi-model fallback
- Implement all 7 analysis layers as **separate functions**, each making one Gemini API call:
  - `analyze_grammar(text)` — Layer 1: Grammar & Language (15%)
  - `analyze_readability(text)` — Layer 2: Readability Score (10%)
  - `analyze_abstract(text)` — Layer 3: Abstract Quality (10%)
  - `analyze_structure(sections)` — Layer 4: Structural Integrity (15%)
  - `analyze_methodology(text)` — Layer 5: Methodology Soundness (15%)
  - `analyze_logic(sections)` — Layer 6: Logical Consistency (15%)
  - `analyze_conclusion(text)` — Layer 7: Conclusion Completeness (10%)
- If a section is empty string `""` — skip that layer, assign 0/10, no Gemini call
- If Gemini returns invalid JSON — retry **once** with stricter prompt, then 0/10 if still fails
- Implement **pure Python scoring** — weighted average math only, no Gemini:
  ```python
  confidence_score = sum(layer_scores[k] * weights[k] for k in weights) * 10
  ```
- Grade mapping via Python dict/if-else — no AI needed for this

**Deliverable (end of Phase 2):**
- Function `run_all_layers(sections: dict) → dict` returns 7 layer scores
- Function `calculate_confidence_score(layer_scores: dict) → dict` returns final score + grade
```json
{
  "final_score": 76.5,
  "grade": "B — Good",
  "layer_breakdown": {
    "grammar": 80,
    "readability": 70,
    "abstract": 90,
    "structure": 80,
    "methodology": 60,
    "logic": 70,
    "conclusion": 80
  }
}
```

**Key reference sections in ResearchSense_Research.md:**
- §3 — All Gemini prompt templates (Layer 1–7)
- §9 — Scoring algorithm with weights and grading scale

---

### 👤 Person 3 — Citations, Report & Frontend

**Files owned:**
```
citation_checker.py  ← Semantic Scholar + CrossRef API integration
report_generator.py  ← ReportLab PDF report generation
frontend/
  ├── index.html     ← upload page with drag-and-drop
  ├── style.css      ← styling
  └── app.js         ← API calls + results display
```

**Responsibilities:**
- Implement citation extraction from the References section
- Integrate Semantic Scholar API for citation existence/credibility check
- Integrate CrossRef API for DOI validation
- Implement citation quality scoring (Layer 8, weight: 10%)
- Build ReportLab PDF report with:
  - Final score + letter grade (prominent, top of report)
  - Per-dimension score breakdown table
  - Specific issues found per layer
  - Actionable suggestions per layer
  - Soft warning section if any paper sections were not detected
- Build HTML/CSS/JS frontend:
  - Drag-and-drop PDF upload with file validation
  - Loading indicator during analysis (30–60 seconds)
  - Results display: score, grade, visual layer breakdown
  - Download button for the PDF report
- Report tone: **professor-facing, formal** — use peer-review language throughout

**Deliverable (end of Phase 4):**
- Complete working application in the browser
- Upload PDF → see results → download report

**Key reference sections in ResearchSense_Research.md:**
- §7 — Semantic Scholar API integration
- §8 — CrossRef API and DOI extraction
- §11 — Frontend HTML/JS templates
- §12 — ReportLab report generation

---

## 4. Integration Plan

### Module Interface Contract

All 3 people must agree on this shared interface before coding starts:

```python
# pdf_parser.py → section_detector.py → main.py
# Section dict format (Person 1 produces, Person 2 & 3 consume):
sections = {
    "abstract": str,       # empty string "" if not found
    "introduction": str,
    "methodology": str,
    "results": str,
    "discussion": str,
    "conclusion": str,
    "references": str
}

# gemini_analyzer.py → scoring.py (Person 2 internal)
# Layer scores dict (Person 2 produces, main.py consumes):
layer_scores = {
    "grammar":      float,   # 0-10
    "readability":  float,
    "abstract":     float,
    "structure":    float,
    "methodology":  float,
    "logic":        float,
    "conclusion":   float,
    "citations":    float    # Person 3 produces this one
}

# Final score output (main.py assembles from P2 + P3):
score_result = {
    "final_score": float,    # 0-100
    "grade":       str,      # "A — Excellent", "B — Good", etc.
    "layer_breakdown": dict  # scores scaled to 0-100
}
```

### Integration Steps (final day)
1. All 3 people push their branches to GitHub
2. Designate one device as the integration machine
3. Pull all branches, merge into `main`
4. Test the full pipeline end-to-end with a real paper
5. Fix any integration bugs together
6. Pre-cache 5 sample paper results as demo backup

---

## 5. Environment Setup (every team member)

```bash
# 1. Clone the GitHub repo
git clone <your-repo-url>
cd researchsense

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install all dependencies
pip install google-generativeai pymupdf fastapi uvicorn python-multipart reportlab requests semanticscholar python-dotenv

# 4. Create your .env file (copy from .env.example)
# Fill in your own GEMINI_API_KEY

# 5. Run the server
uvicorn main:app --reload
# Visit http://localhost:8000/docs to test
```

**⚠️ IMPORTANT: Never push `.env` to GitHub. It's already in `.gitignore`.**

---

## 6. Phase Timeline

| Phase | Owner | Goal | Target |
|-------|-------|------|--------|
| Phase 1 | Person 1 | FastAPI + PDF extraction + section detection | Week 1–2 |
| Phase 2 | Person 2 | 7 Gemini analysis layers + scoring | Week 2–4 |
| Phase 3 | Person 3 | Citations (Semantic Scholar + CrossRef) | Week 4–5 |
| Phase 4 | Person 3 | ReportLab PDF report + Web UI | Week 5–6 |
| Integration | All 3 | Merge, test, fix, demo prep | Week 6 |

---

## 7. Demo Day Strategy

1. **Pre-analyze 5–10 real papers** and cache the results (insurance against API downtime)
2. **Live demo:** Use a short (4–6 page) paper to minimize Gemini API calls
3. **Have screenshots** of full reports as a backup if APIs are slow
4. **Show the professor-facing report** prominently — this is the main UX for evaluators
5. Free tier allows ~30 full paper analyses per day — more than enough

---

*ResearchSense Team Summary — April 2026*
*Share this document with all team members before development begins*
