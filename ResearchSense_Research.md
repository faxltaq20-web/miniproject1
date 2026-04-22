# ResearchSense — Complete Project Research Document
**AI-Based Academic Paper Analysis and Error Detection System**  
*Research compiled: April 2026 | Domain: AI + EdTech*

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Gemini API — Core AI Engine](#3-gemini-api--core-ai-engine)
4. [PDF Parsing — PyMuPDF](#4-pdf-parsing--pymupdf)
5. [Section Detection](#5-section-detection)
6. [Evaluation Parameters (8 Layers)](#6-evaluation-parameters-8-layers)
7. [Semantic Scholar API — Citation Check](#7-semantic-scholar-api--citation-check)
8. [CrossRef API — DOI Validation](#8-crossref-api--doi-validation)
9. [Scoring Algorithm](#9-scoring-algorithm)
10. [Backend — FastAPI](#10-backend--fastapi)
11. [Frontend](#11-frontend)
12. [Report Generation — ReportLab](#12-report-generation--reportlab)
13. [Full Tech Stack Summary](#13-full-tech-stack-summary)
14. [Installation & Setup Guide](#14-installation--setup-guide)
15. [Project Timeline](#15-project-timeline)
16. [Risks & Mitigations](#16-risks--mitigations)

---

## 1. Project Overview

### What is ResearchSense?
ResearchSense is an AI-powered academic paper reviewer. A user uploads a research paper PDF, and the system automatically analyzes it across 8 quality dimensions, then generates a structured report with a confidence score (0–100).

### Core Flow
```
User uploads PDF
      ↓
Text Extraction (PyMuPDF)
      ↓
Section Splitting (Rule-based Python)
      ↓
8-Layer Analysis (Gemini API + Semantic Scholar + CrossRef)
      ↓
Scoring Algorithm (Custom Python)
      ↓
Report Generation (ReportLab PDF)
      ↓
Display in Web UI
```

### Target Users
- University students submitting research papers
- Researchers preparing journal submissions
- Academics who want pre-review quality checks

---

## 2. System Architecture

### Full Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (HTML/CSS/JS)               │
│              Upload Form + Report Display UI             │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP POST (PDF file)
┌──────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI)                       │
│   /upload endpoint → orchestrates entire pipeline        │
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

---

## 3. Gemini API — Core AI Engine

### Why Gemini?
- Completely **free tier** — no credit card required
- Large **1 million token context window** — can handle entire research papers
- Strong at structured JSON output — perfect for layer-by-layer analysis
- Fast response time with Gemini 2.5 Flash

### Current Free Tier Limits (April 2026)

| Model | RPM | RPD | TPM | Best For |
|---|---|---|---|---|
| Gemini 2.5 Flash | 10 | 250 | 250,000 | **Recommended for this project** |
| Gemini 2.5 Flash-Lite | 15 | 1,000 | 250,000 | High-volume, simpler tasks |
| Gemini 2.5 Pro | 5 | 100 | 250,000 | Complex reasoning (very limited) |

> ⚠️ **Important Note:** Google reduced free tier limits by 50-80% in December 2025. Gemini 2.0 Flash was deprecated in March 2026. Use **Gemini 2.5 Flash** as your primary model.

> ⚠️ **Rate Limit Strategy:** Since each paper analysis uses ~6-8 API calls (one per layer), with 250 RPD you can analyze ~30 full papers per day on the free tier. This is more than enough for a university demo.

### Getting Your Free API Key
1. Go to **aistudio.google.com**
2. Sign in with Google account
3. Click **"Get API Key"** → Create API key
4. Copy and store in your `.env` file as `GEMINI_API_KEY=your_key_here`

### Installation
```bash
pip install google-generativeai
```

### Basic Setup Code
```python
import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-2.5-flash")

# Test call
response = model.generate_content("Say hello")
print(response.text)
```

### Prompt Templates for Each Layer

**Layer 1 — Grammar & Language Check:**
```python
prompt = f"""
You are an expert academic editor. Analyze the following section of a research paper.
Detect ALL grammar, spelling, punctuation, and clarity errors.

For each error found, return a JSON object with:
- "sentence": the problematic sentence
- "error_type": one of [grammar, spelling, clarity, punctuation, word_choice]
- "correction": the suggested fix
- "severity": one of [low, medium, high]

Return ONLY a valid JSON array. No extra text.

Section Text:
{section_text}
"""
```

**Layer 2 — Readability Score:**
```python
prompt = f"""
You are an academic writing expert. Analyze the readability of the following research paper section.

Evaluate:
1. Sentence length (are sentences too long/complex?)
2. Vocabulary complexity (is jargon excessive?)
3. Clarity of expression
4. Overall accessibility for the target academic audience

Return ONLY a JSON object with:
- "readability_score": integer from 0 to 10 (10 = very readable)
- "average_sentence_complexity": one of [simple, moderate, complex, very_complex]
- "main_issues": list of up to 3 specific readability problems found
- "suggestions": list of up to 3 concrete improvements

Section Text:
{section_text}
"""
```

**Layer 3 — Abstract Quality:**
```python
prompt = f"""
You are a senior academic reviewer. Evaluate the quality of the following Abstract.

A high-quality abstract must include ALL of these elements:
1. Research problem / objective
2. Methodology used
3. Key results / findings
4. Conclusion / implications

Check each element and score the abstract.

Return ONLY a JSON object with:
- "score": integer from 0 to 10
- "elements_present": dict with keys [problem, methodology, results, conclusion] each true/false
- "word_count": integer
- "is_standalone": true/false (can it be understood without reading the full paper?)
- "missing_elements": list of what is missing
- "improvement_suggestions": list of up to 3 specific suggestions

Abstract:
{abstract_text}
"""
```

**Layer 4 — Structural Integrity:**
```python
prompt = f"""
You are an academic paper structure expert. Analyze the structural integrity of this research paper.

Check for the presence and quality of these standard sections:
- Abstract
- Keywords
- Introduction
- Literature Review / Related Work
- Methodology
- Results / Findings
- Discussion
- Conclusion
- References

Return ONLY a JSON object with:
- "score": integer from 0 to 10
- "sections_found": list of section names detected
- "sections_missing": list of sections that should be present but aren't
- "order_correct": true/false (are sections in logical order?)
- "structural_issues": list of specific problems found
- "suggestions": list of improvements

Full Paper Text (first 3000 words):
{paper_text[:3000]}
"""
```

**Layer 5 — Methodology Soundness:**
```python
prompt = f"""
You are an expert research methodology reviewer. Critically analyze the Methodology section below.

Evaluate:
1. Is the research design clearly described?
2. Are tools, datasets, or instruments appropriate and justified?
3. Is the sample size or dataset sufficient and explained?
4. Are limitations of the methodology acknowledged?
5. Can the methodology be replicated by other researchers?

Return ONLY a JSON object with:
- "score": integer from 0 to 10
- "design_clarity": true/false
- "tools_justified": true/false
- "sample_size_explained": true/false
- "limitations_mentioned": true/false
- "reproducibility": one of [high, medium, low]
- "issues_found": list of specific weaknesses
- "suggestions": list of up to 4 improvements

Methodology Section:
{methodology_text}
"""
```

**Layer 6 — Logical Consistency:**
```python
prompt = f"""
You are a senior peer reviewer. Compare the Abstract, Methodology, Results, and Conclusion
of this research paper for logical consistency.

Check for:
1. Do the Results actually prove what the Abstract claims?
2. Do the Methods logically lead to the Results reported?
3. Does the Conclusion accurately reflect what the Results show?
4. Are there any unsupported claims or contradictions between sections?

Return ONLY a JSON object with:
- "score": integer from 0 to 10
- "abstract_results_aligned": true/false
- "methods_results_aligned": true/false
- "results_conclusion_aligned": true/false
- "contradictions_found": list of specific contradictions (empty list if none)
- "unsupported_claims": list of claims not backed by results (empty list if none)
- "consistency_level": one of [high, medium, low]
- "suggestions": list of improvements

Abstract: {abstract_text}

Methodology: {methodology_text}

Results: {results_text}

Conclusion: {conclusion_text}
"""
```

**Layer 7 — Conclusion Completeness:**
```python
prompt = f"""
You are an expert academic reviewer. Evaluate the quality and completeness of this Conclusion section.

A strong conclusion must:
1. Directly answer the original research question
2. Summarize key findings clearly
3. Discuss implications and significance of findings
4. Mention limitations of the study
5. Suggest directions for future research

Return ONLY a JSON object with:
- "score": integer from 0 to 10
- "answers_research_question": true/false
- "summarizes_findings": true/false
- "discusses_implications": true/false
- "mentions_limitations": true/false
- "suggests_future_work": true/false
- "issues_found": list of specific weaknesses
- "suggestions": list of improvements

Conclusion Section:
{conclusion_text}
"""
```

### Handling Gemini API Rate Limits
```python
import time

def call_gemini_with_retry(model, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):  # Rate limit hit
                wait_time = 60 * (attempt + 1)  # Wait 60s, 120s, 180s
                print(f"Rate limit hit. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("Max retries exceeded")
```

---

## 4. PDF Parsing — PyMuPDF

### Why PyMuPDF?
- Best performance for native (non-scanned) PDF extraction
- Handles multi-column academic paper layouts
- Free and open-source (AGPL license)
- Supports OCR via Tesseract for scanned PDFs
- Has `pymupdf4llm` extension optimized for LLM/AI pipelines

### Installation
```bash
pip install pymupdf
pip install pymupdf4llm   # Optional: better for LLM pipelines
```

### Basic Text Extraction
```python
import pymupdf

def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    full_text = ""
    
    for page in doc:
        full_text += page.get_text()
    
    doc.close()
    return full_text
```

### Advanced Extraction (Multi-column Academic Papers)
```python
import pymupdf4llm

def extract_text_smart(pdf_path):
    # Converts to markdown format — better for section detection
    md_text = pymupdf4llm.to_markdown(pdf_path)
    return md_text
```

### Handling Scanned PDFs (OCR Fallback)
```python
import pymupdf

def extract_with_ocr_fallback(pdf_path):
    doc = pymupdf.open(pdf_path)
    full_text = ""
    
    for page in doc:
        text = page.get_text()
        
        # If page has no extractable text, use OCR
        if len(text.strip()) < 50:
            tp = page.get_textpage_ocr()
            text = page.get_text(textpage=tp)
        
        full_text += text
    
    return full_text
```

### Key Limitations to Know
- Cannot extract text from scanned PDFs without OCR integration
- Multi-column layouts may have text ordering issues
- Some PDFs use fonts without character maps — text may appear garbled

---

## 5. Section Detection

### Strategy: Rule-Based Regex + Heading Detection

Academic papers follow predictable heading patterns. We use regex to identify section boundaries.

```python
import re

SECTION_PATTERNS = {
    "abstract": r"\b(abstract)\b",
    "introduction": r"\b(1\.?\s*introduction|introduction)\b",
    "literature_review": r"\b(2\.?\s*(literature review|related work|background))\b",
    "methodology": r"\b(\d\.?\s*(methodology|methods|method|approach|experimental setup))\b",
    "results": r"\b(\d\.?\s*(results|findings|experiments|evaluation))\b",
    "discussion": r"\b(\d\.?\s*(discussion|analysis))\b",
    "conclusion": r"\b(\d\.?\s*(conclusion|conclusions|summary|closing remarks))\b",
    "references": r"\b(references|bibliography|works cited)\b"
}

def detect_sections(full_text):
    lines = full_text.split('\n')
    sections = {k: "" for k in SECTION_PATTERNS}
    current_section = None
    
    for line in lines:
        line_lower = line.strip().lower()
        
        # Check if this line is a section header
        for section_name, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, line_lower):
                current_section = section_name
                break
        
        # Add line to current section
        if current_section:
            sections[current_section] += line + "\n"
    
    return sections
```

### Fallback: Ask Gemini to Split Sections
If regex fails (which can happen with unusual paper formats), use Gemini:

```python
def detect_sections_with_ai(full_text, model):
    prompt = f"""
    The following is a research paper. Split it into these sections:
    abstract, introduction, methodology, results, conclusion, references.
    
    Return ONLY a JSON object where keys are section names and values are the section text.
    
    Paper:
    {full_text[:8000]}
    """
    response = model.generate_content(prompt)
    import json
    return json.loads(response.text)
```

---

## 6. Evaluation Parameters (8 Layers)

Research-backed criteria drawn from peer review standards at 11 top-tier CS conferences and a four-dimensional framework (technical content, structural coherence, writing precision, ethical integrity).

### Parameter Weights

| # | Parameter | Weight | API Used |
|---|---|---|---|
| 1 | Grammar & Language | 15% | Gemini API |
| 2 | Readability Score | 10% | Gemini API |
| 3 | Abstract Quality | 10% | Gemini API |
| 4 | Structural Integrity | 15% | Gemini API |
| 5 | Methodology Soundness | 15% | Gemini API |
| 6 | Logical Consistency | 15% | Gemini API |
| 7 | Conclusion Completeness | 10% | Gemini API |
| 8 | Citation & Reference Quality | 10% | Semantic Scholar + CrossRef |

### What Each Parameter Checks

**1. Grammar & Language (15%)**
- Spelling and grammar errors
- Sentence clarity and conciseness
- Passive vs active voice overuse
- Academic tone appropriateness
- Word choice and vocabulary

**2. Readability Score (10%)**
- Average sentence length and complexity
- Jargon density and accessibility
- Flesch Reading Ease estimation
- Clarity for target academic audience
- Research shows 26%+ of scientific abstracts are now beyond college-graduate reading level

**3. Abstract Quality (10%)**
- Presence of: problem statement, methodology, results, conclusion
- Is the abstract self-contained (standalone)?
- Word count within appropriate limits (150–300 words)
- All key contributions mentioned

**4. Structural Integrity (15%)**
- Are all required sections present?
- Are sections in the correct logical order?
- Presence of Keywords section
- Presence and formatting of headings
- Adherence to standard paper structure

**5. Methodology Soundness (15%)**
- Is the research design clearly described?
- Are tools/datasets/instruments appropriate and justified?
- Is sample size or dataset size explained?
- Are methodology limitations acknowledged?
- Is the methodology reproducible?

**6. Logical Consistency (15%)**
- Do Results prove what the Abstract claims?
- Does Methodology logically lead to Results?
- Does Conclusion accurately reflect Results?
- No contradictions between sections
- No unsupported or overreaching claims

**7. Conclusion Completeness (10%)**
- Directly answers the research question
- Summarizes key findings clearly
- Discusses implications of findings
- Acknowledges study limitations
- Suggests future research directions

**8. Citation & Reference Quality (10%)**
- Citations actually exist (verified via Semantic Scholar)
- DOIs are valid (verified via CrossRef)
- References are properly formatted
- No self-citation abuse
- References are recent and relevant

---

## 7. Semantic Scholar API — Citation Check

### What It Does
Verifies that references cited in the paper actually exist in the academic literature database covering 200M+ papers.

### Access & Limits
- **Completely free** — no payment required
- Public API: 1 request/second (unauthenticated)
- With free API key: 1 RPS on all endpoints (more stable)
- Get API key at: api.semanticscholar.org

### Installation
```bash
pip install semanticscholar
```

### Usage — Search for a Paper
```python
from semanticscholar import SemanticScholar

sch = SemanticScholar()

# Search by title
results = sch.search_paper("Attention is All You Need", limit=1)

if results:
    paper = results[0]
    print(f"Title: {paper.title}")
    print(f"Year: {paper.year}")
    print(f"Authors: {[a.name for a in paper.authors]}")
    print(f"Citations: {paper.citationCount}")
    print(f"Found: True")
else:
    print("Paper NOT FOUND in database")
```

### Usage — Batch Citation Verification
```python
def verify_citations(reference_list):
    sch = SemanticScholar()
    results = []
    
    for ref in reference_list:
        try:
            search = sch.search_paper(ref['title'], limit=1)
            
            if search and len(search) > 0:
                paper = search[0]
                results.append({
                    "title": ref['title'],
                    "found": True,
                    "year": paper.year,
                    "citation_count": paper.citationCount,
                    "is_credible": paper.citationCount > 5,  # cited at least 5 times
                    "authors_match": True  # can add author matching logic
                })
            else:
                results.append({
                    "title": ref['title'],
                    "found": False,
                    "is_credible": False
                })
                
            time.sleep(1)  # Respect rate limit: 1 request/second
            
        except Exception as e:
            results.append({
                "title": ref['title'],
                "found": False,
                "error": str(e)
            })
    
    return results
```

### Citation Score Calculation
```python
def calculate_citation_score(verified_citations):
    if not verified_citations:
        return 5  # neutral if no citations

    found_count = sum(1 for c in verified_citations if c['found'])
    credible_count = sum(1 for c in verified_citations if c.get('is_credible', False))
    total = len(verified_citations)

    found_ratio = found_count / total          # % of citations that exist
    credible_ratio = credible_count / total    # % that are credible

    score = (found_ratio * 6) + (credible_ratio * 4)  # Max = 10
    return round(score, 1)
```

---

## 8. CrossRef API — DOI Validation

### What It Does
CrossRef is the official DOI registry for academic publications. It validates whether DOIs in a paper's references are real and returns full metadata.

### Access & Limits
- **Completely free** — no API key required
- Polite pool: include your email as `mailto` parameter for better performance
- No formal rate limit — be respectful (1-2 requests/second max)
- Base URL: `https://api.crossref.org`

### Installation
```bash
pip install requests
# Optional: pip install habanero  (Python CrossRef wrapper)
```

### DOI Extraction from References
```python
import re

def extract_dois_from_references(references_text):
    # Common DOI patterns
    doi_pattern = r'\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b'
    dois = re.findall(doi_pattern, references_text, re.IGNORECASE)
    return list(set(dois))  # deduplicate
```

### DOI Validation
```python
import requests
import time

def validate_doi(doi, your_email="your@email.com"):
    url = f"https://api.crossref.org/works/{doi}"
    headers = {"User-Agent": f"ResearchSense/1.0 (mailto:{your_email})"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            work = data.get("message", {})
            return {
                "doi": doi,
                "valid": True,
                "title": work.get("title", ["Unknown"])[0],
                "year": work.get("published", {}).get("date-parts", [[None]])[0][0],
                "publisher": work.get("publisher", "Unknown"),
                "type": work.get("type", "Unknown")
            }
        else:
            return {"doi": doi, "valid": False, "status_code": response.status_code}
            
    except Exception as e:
        return {"doi": doi, "valid": False, "error": str(e)}
    finally:
        time.sleep(1)  # Be polite to CrossRef servers

def validate_all_dois(dois, your_email):
    results = []
    for doi in dois:
        result = validate_doi(doi, your_email)
        results.append(result)
    return results
```

---

## 9. Scoring Algorithm

### Weighted Average Formula
```python
WEIGHTS = {
    "grammar":         0.15,
    "readability":     0.10,
    "abstract":        0.10,
    "structure":       0.15,
    "methodology":     0.15,
    "logic":           0.15,
    "conclusion":      0.10,
    "citations":       0.10
}

def calculate_confidence_score(layer_scores: dict) -> dict:
    """
    layer_scores: dict with keys matching WEIGHTS, values 0-10
    Returns: dict with final score and grade
    """
    if not layer_scores:
        return {"score": 0, "grade": "F"}

    weighted_sum = 0
    for layer, weight in WEIGHTS.items():
        score = layer_scores.get(layer, 0)
        weighted_sum += score * weight

    # Scale from 0-10 to 0-100
    final_score = round(weighted_sum * 10, 1)

    # Assign grade
    if final_score >= 85:
        grade = "A — Excellent"
    elif final_score >= 70:
        grade = "B — Good"
    elif final_score >= 55:
        grade = "C — Needs Improvement"
    elif final_score >= 40:
        grade = "D — Poor"
    else:
        grade = "F — Very Poor"

    return {
        "final_score": final_score,
        "grade": grade,
        "layer_breakdown": {k: round(v * 10, 1) for k, v in layer_scores.items()},
        "weights_used": WEIGHTS
    }
```

### Example Scoring Run
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
Final Score:               76.5 / 100  →  Grade: B — Good
```

---

## 10. Backend — FastAPI

### Why FastAPI?
- Python-native — same language as all other components
- Auto-generates interactive API docs at `/docs`
- Async support — handles file uploads efficiently
- Very fast and production-ready
- Used by Netflix, Uber, and Microsoft

### Installation
```bash
pip install fastapi uvicorn python-multipart
```

### Core API Structure
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import tempfile
import os

app = FastAPI(title="ResearchSense API", version="1.0.0")

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ResearchSense API is running"}

@app.post("/analyze")
async def analyze_paper(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are accepted"})
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Run full pipeline
        text = extract_text_from_pdf(tmp_path)
        sections = detect_sections(text)
        layer_scores = run_all_layers(sections)
        score_result = calculate_confidence_score(layer_scores)
        report = generate_report(sections, layer_scores, score_result)
        
        return {
            "filename": file.filename,
            "score": score_result,
            "layer_results": layer_scores,
            "report_url": report
        }
    finally:
        os.unlink(tmp_path)  # Delete temp file

# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Running the Server
```bash
uvicorn main:app --reload
# Access API docs at: http://localhost:8000/docs
```

---

## 11. Frontend

### Recommended: Simple HTML + CSS + JavaScript

For a university project, a clean single-page HTML app is more than sufficient. No React needed unless you want it.

### Minimal Frontend Structure
```
frontend/
├── index.html       ← Main upload page
├── result.html      ← Report display page
├── style.css        ← Styling
└── app.js           ← API call logic
```

### Upload Form (index.html core)
```html
<div class="upload-section">
    <h1>ResearchSense</h1>
    <p>Upload your research paper for AI-powered analysis</p>
    
    <div class="drop-zone" id="dropZone">
        <input type="file" id="fileInput" accept=".pdf" hidden>
        <p>📄 Drag & drop your PDF here or <span onclick="document.getElementById('fileInput').click()">browse</span></p>
    </div>
    
    <button id="analyzeBtn" onclick="analyzePaper()">Analyze Paper</button>
    
    <div id="loading" style="display:none">
        <p>🔍 Analyzing your paper... This may take 30–60 seconds.</p>
        <progress></progress>
    </div>
</div>
```

### API Call (app.js)
```javascript
async function analyzePaper() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a PDF file first');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    document.getElementById('loading').style.display = 'block';
    
    try {
        const response = await fetch('http://localhost:8000/analyze', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        displayResults(result);
    } catch (error) {
        alert('Error analyzing paper: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function displayResults(result) {
    const score = result.score.final_score;
    const grade = result.score.grade;
    document.getElementById('finalScore').textContent = `${score}/100`;
    document.getElementById('grade').textContent = grade;
    // Render layer breakdown...
}
```

---

## 12. Report Generation — ReportLab

### Installation
```bash
pip install reportlab
```

### Generate PDF Report
```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_pdf_report(paper_filename, score_result, layer_results, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph("ResearchSense Analysis Report", styles['Title']))
    story.append(Paragraph(f"Paper: {paper_filename}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Final Score
    story.append(Paragraph(
        f"Final Confidence Score: {score_result['final_score']}/100 ({score_result['grade']})",
        styles['Heading1']
    ))
    story.append(Spacer(1, 12))
    
    # Layer Scores Table
    table_data = [["Parameter", "Score", "Weight"]]
    for layer, score in layer_results.items():
        weight = f"{int(WEIGHTS[layer]*100)}%"
        table_data.append([layer.title(), f"{score}/10", weight])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(table)
    
    doc.build(story)
    return output_path
```

---

## 13. Full Tech Stack Summary

| Component | Tool | Version | Cost |
|---|---|---|---|
| AI Analysis Engine | Google Gemini 2.5 Flash | Latest | ✅ Free |
| Citation Verification | Semantic Scholar API | Latest | ✅ Free |
| DOI Validation | CrossRef REST API | Latest | ✅ Free |
| PDF Parsing | PyMuPDF | 1.27.x | ✅ Free |
| Text Processing | pymupdf4llm | Latest | ✅ Free |
| Backend Framework | FastAPI | 0.115.x | ✅ Free |
| ASGI Server | Uvicorn | Latest | ✅ Free |
| Report Generation | ReportLab | 4.x | ✅ Free |
| Frontend | HTML + CSS + JS | — | ✅ Free |
| Python SDK (Gemini) | google-generativeai | Latest | ✅ Free |
| Python SDK (S2) | semanticscholar | 0.12.x | ✅ Free |

### One-Line Install
```bash
pip install google-generativeai pymupdf pymupdf4llm fastapi uvicorn python-multipart reportlab requests semanticscholar
```

---

## 14. Installation & Setup Guide

### Step 1 — Clone/Create Project
```bash
mkdir researchsense
cd researchsense
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Step 2 — Install Dependencies
```bash
pip install google-generativeai pymupdf pymupdf4llm fastapi uvicorn python-multipart reportlab requests semanticscholar
```

### Step 3 — Environment Variables
Create a `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key_here
CONTACT_EMAIL=your@email.com
```

Load in Python:
```python
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
```

Also install dotenv:
```bash
pip install python-dotenv
```

### Step 4 — Project Structure
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
├── .env
└── requirements.txt
```

### Step 5 — Run the App
```bash
uvicorn main:app --reload
# Visit http://localhost:8000/docs to test API
# Open frontend/index.html in browser
```

---

## 15. Project Timeline

| Phase | Task | Duration |
|---|---|---|
| Phase 1 | Setup environment, API keys, project structure | 2–3 days |
| Phase 2 | PDF parser + section detector | 3–4 days |
| Phase 3 | Gemini API integration (7 layers) | 5–7 days |
| Phase 4 | Citation checking (Semantic Scholar + CrossRef) | 2–3 days |
| Phase 5 | Scoring algorithm | 1–2 days |
| Phase 6 | ReportLab PDF report generation | 2–3 days |
| Phase 7 | Frontend UI | 3–4 days |
| Phase 8 | Testing on real papers + bug fixes | 3–4 days |
| **Total** | | **~3–4 weeks** |

---

## 16. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Gemini free tier runs out (250 RPD) | Medium | Use Flash-Lite for simple layers; cache results |
| PDF with unusual format breaks parser | Medium | Add Gemini-based fallback section detection |
| Semantic Scholar API slow/down | Low | Add 3s timeout + retry logic; cache results |
| CrossRef API rate limiting | Low | Add `mailto` param for polite pool; add delays |
| Scanned PDF with no extractable text | Medium | Use pymupdf4llm OCR fallback |
| Gemini returns invalid JSON | Medium | Wrap in try/except; ask Gemini to retry with stricter prompt |
| Paper has non-standard section names | Medium | Use Gemini as fallback section detector |

### Rate Limit Strategy for Demo Day
When presenting to university:
1. Pre-analyze 5–10 sample papers and cache results
2. Show live analysis on a short 4-page paper (fewer tokens)
3. Have screenshots of full reports as backup

---

*Document prepared for ResearchSense — AI-Based Academic Paper Analysis and Error Detection System*  
*Last updated: April 2026*
