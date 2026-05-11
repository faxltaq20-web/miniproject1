---
phase: 1
plan: 1
title: "Person 1 — Backend Core & PDF Pipeline"
owner: "Person 1 (P1)"
wave: 1
depends_on: []
files_modified:
  - main.py
  - pdf_parser.py
  - section_detector.py
  - requirements.txt
  - .env.example
requirements:
  - CORE-01
  - CORE-02
  - CORE-03
  - CORE-04
autonomous: true
---

# Plan 01: Person 1 — Backend Core & PDF Pipeline

## Objective

Person 1 builds the entire backend foundation for ResearchSense: project scaffolding, FastAPI skeleton with the `/analyze` endpoint, PDF text extraction using basic PyMuPDF `get_text()`, and regex-only section detection. This is the core pipeline that all other team members will consume.

## Owner

**Person 1 (P1)** — Backend Core & PDF Pipeline

---

## Processing Pipeline

```
User uploads PDF via POST /analyze
        ↓
[main.py] Validate file is .pdf
        ↓
[pdf_parser.py] Extract text using PyMuPDF get_text()
        ↓
    Text < 100 chars? → Return 422 error (not a text-based PDF)
        ↓
[section_detector.py] Regex-only section detection
        ↓
    Missing key sections? → Add soft warnings (but proceed)
        ↓
Return JSON: { filename, sections, section_count, warnings }
```



## Tasks

### Task 1: Project Scaffolding & Dependencies

**Read first:**
- `ResearchSense_Research.md` (Section 14 — Installation & Setup Guide)
- `TEAM_SUMMARY.md` (Section 5 — Environment Setup)
- `.gitignore`

**Action:**

Create the following files in the project root:

**requirements.txt:**
```
google-generativeai
pymupdf
fastapi
uvicorn
python-multipart
reportlab
requests
semanticscholar
python-dotenv
```

> **Note:** `pymupdf4llm` is NOT included — we use basic `get_text()` only for MVP.

**.env.example:**
```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
CONTACT_EMAIL=your_email@example.com
```

> **Note:** Single model only — no `GEMINI_MODEL_FALLBACK`. Multi-model orchestration is future scope.

Verify `.gitignore` already contains `.env` — if not, add it.

Create a personal `.env` file (not committed) with your actual `GEMINI_API_KEY`.

**Acceptance criteria:**
- `requirements.txt` exists with all 9 packages (no `pymupdf4llm`)
- `.env.example` exists with `GEMINI_API_KEY=`, `GEMINI_MODEL=`, `CONTACT_EMAIL=`
- `.gitignore` contains `.env`
- `pip install -r requirements.txt` succeeds in a fresh venv

---

### Task 2: FastAPI Application Skeleton (main.py)

**Read first:**
- `ResearchSense_Research.md` (Section 10 — Backend FastAPI)
- `TEAM_SUMMARY.md` (Section 3 — Person 1 Responsibilities)
- `01-CONTEXT.md` (Decisions D-08, D-09, D-10, D-11)

**Action:**

Create `main.py` with:

1. **Imports:** `FastAPI`, `UploadFile`, `File`, `CORSMiddleware`, `JSONResponse`, `tempfile`, `os`, `dotenv`
2. **Load `.env`** using `from dotenv import load_dotenv; load_dotenv()`
3. **FastAPI app** with `title="ResearchSense API"`, `version="1.0.0"`
4. **CORS middleware:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```
5. **Health check endpoint:** `GET /` → returns `{"status": "ResearchSense API is running"}`
6. **Analyze endpoint:** `POST /analyze` that:
   - Accepts `file: UploadFile = File(...)`
   - Validates file is `.pdf` — returns 400 if not:
     ```python
     {"error": "Only PDF files are accepted"}
     ```
   - Saves uploaded file to a temp file
   - Calls `pdf_parser.extract_text(tmp_path)` to get raw text
   - If extraction returns empty/short text, returns 422:
     ```python
     {
         "error": "Text extraction failed",
         "message": "Could not extract text from this PDF. Please ensure it is a text-based PDF."
     }
     ```
   - Calls `section_detector.detect_sections(text)` to get sections dict
   - **No strict section rejection** — proceed with whatever sections were detected. Add a soft warning listing any missing key sections:
     ```python
     warnings = []
     for s in ["abstract", "methodology", "conclusion"]:
         if not sections.get(s, "").strip():
             warnings.append(s)
     ```
   - Returns success response:
     ```python
     {
         "filename": file.filename,
         "sections": sections,
         "section_count": len([v for v in sections.values() if v.strip()]),
         "warnings": warnings
     }
     ```
   - Cleans up temp file in a `finally` block
7. **`if __name__ == "__main__":`** block with `uvicorn.run(app, host="0.0.0.0", port=8000)`

> **Note:** Phase 1 returns only sections JSON. AI analysis (Person 2) and citation checking (Person 3) will be wired into `main.py` in later phases.

**Acceptance criteria:**
- `main.py` loads `.env` via `load_dotenv()`
- `main.py` has CORS middleware with `allow_origins=["*"]`
- `GET /` returns `{"status": "ResearchSense API is running"}`
- `POST /analyze` accepts PDF uploads
- Non-PDF files get 400 error
- Empty/scanned PDFs get 422 error
- Missing sections produce a **soft warning** (not a hard rejection) — analysis still proceeds
- Response includes `filename`, `sections`, `section_count`, `warnings`
- Temp file is cleaned up in `finally` block
- `uvicorn main:app --reload` starts on port 8000

---

### Task 3: PDF Text Extraction (pdf_parser.py)

**Read first:**
- `ResearchSense_Research.md` (Section 4 — PDF Parsing PyMuPDF)
- `01-CONTEXT.md` (Decisions D-01, D-02, D-03)

**Action:**

Create `pdf_parser.py` with a single function:

```python
import pymupdf

def extract_text(pdf_path: str) -> str:
    """Extract plain text from a PDF file using PyMuPDF."""
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    if len(text.strip()) < 100:
        raise ValueError(
            "Could not extract text from this PDF. Please ensure it is a text-based PDF."
        )

    return text
```

Key points:
- **Basic `get_text()` only** — no `pymupdf4llm`, no Markdown pipeline
- **No OCR** — text-based PDFs only
- Raises `ValueError` if extracted text is < 100 chars (likely scanned/image PDF)

**Acceptance criteria:**
- `pdf_parser.py` has `def extract_text(pdf_path: str) -> str`
- Imports `pymupdf` only — no `pymupdf4llm` import
- Raises `ValueError` when text < 100 chars
- Does NOT import tesseract or any OCR library
- Returns non-empty string for a valid text-based PDF

---

### Task 4: Regex-Only Section Detection (section_detector.py)

**Read first:**
- `ResearchSense_Research.md` (Section 5 — Section Detection)
- `01-CONTEXT.md` (Decisions D-04, D-05, D-06, D-07)

**Action:**

Create `section_detector.py` with:

1. **`SECTION_PATTERNS` dict** — regex patterns for each section:
   ```python
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
   ```

2. **`detect_sections(text: str) -> dict`** — the only public function, **regex only**:
   - Splits text by lines
   - Iterates through lines, matching against `SECTION_PATTERNS` (case-insensitive)
   - When a section header is found, all subsequent lines go to that section until the next header
   - Returns dict with all section keys — empty string `""` for any section not found
   - **No Gemini fallback** — if regex finds 0 sections, return the dict with empty values

Output dict format (must match interface contract from `TEAM_SUMMARY.md`):
```python
{
    "abstract": str,
    "introduction": str,
    "methodology": str,
    "results": str,
    "discussion": str,
    "conclusion": str,
    "references": str
}
```

**Acceptance criteria:**
- Has `SECTION_PATTERNS` dict with 8 regex patterns
- Has `def detect_sections(text: str) -> dict` as the **only** public function
- **No `detect_sections_gemini` function** — no Gemini in this file at all
- Correctly identifies `"1. Introduction"`, `"Abstract"`, `"3. Methodology"` etc.
- Missing sections return `""` — not an error
- Output dict always has all 7 keys (abstract through references)

---

## Verification

### Must-Haves
1. ✓ FastAPI starts and accepts PDF upload on `/analyze`
2. ✓ Basic PyMuPDF `get_text()` extracts text from a real PDF
3. ✓ Regex-only section detection splits text into sections dict
4. ✓ JSON response includes sections + warnings list
5. ✓ Missing sections produce a soft warning (not a hard rejection)
6. ✓ Empty/scanned PDFs return a clear error message
7. ✓ All config via `.env` — no hardcoded secrets

### Test Commands
```bash
# 1. Start server
uvicorn main:app --reload

# 2. Health check
curl http://localhost:8000/

# 3. Upload a real PDF
curl -X POST http://localhost:8000/analyze -F "file=@sample_paper.pdf"

# 4. Upload a non-PDF (should get 400)
curl -X POST http://localhost:8000/analyze -F "file=@readme.txt"
```
