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
  - .gitignore
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

## Tasks

### Task 1: Project Scaffolding & Dependencies

<read_first>
- ResearchSense_Research.md (Section 14 — Installation & Setup Guide)
- TEAM_SUMMARY.md (Section 5 — Environment Setup)
- .gitignore
</read_first>

<action>
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

**.env.example:**
```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
CONTACT_EMAIL=your_email@example.com
```

Verify `.gitignore` already contains `.env` — if not, add it.

Create a personal `.env` file (not committed) with your actual `GEMINI_API_KEY`.
</action>

<acceptance_criteria>
- `requirements.txt` exists and contains all 9 packages listed above (`pymupdf4llm` is NOT included)
- `.env.example` exists and contains `GEMINI_API_KEY=`, `GEMINI_MODEL=`, `CONTACT_EMAIL=`
- `.gitignore` contains `.env`
- Running `pip install -r requirements.txt` in a fresh venv succeeds without errors
</acceptance_criteria>

---

### Task 2: FastAPI Application Skeleton (main.py)

<read_first>
- ResearchSense_Research.md (Section 10 — Backend FastAPI)
- TEAM_SUMMARY.md (Section 3 — Person 1 Responsibilities)
- .planning/phases/01-environment-pdf-parser/01-CONTEXT.md (Decisions D-08, D-09, D-10, D-11)
</read_first>

<action>
Create `main.py` with:

1. **Imports:** FastAPI, UploadFile, File, CORSMiddleware, JSONResponse, tempfile, os, dotenv
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
   - Validates file is `.pdf` — returns 400 with `{"error": "Only PDF files are accepted"}` if not
   - Saves to temp file
   - Calls `pdf_parser.extract_text(tmp_path)` to get raw text
   - Calls `section_detector.detect_sections(text)` to get sections dict
   - If extraction returns empty text, returns 422 with:
     ```python
     {
         "error": "Text extraction failed",
         "message": "Could not extract text from this PDF. Please ensure it is a text-based PDF."
     }
     ```
   - **No strict section rejection** — proceed with whatever sections were detected; add a soft warning if any key sections are missing:
     ```python
     warnings = []
     for s in ["abstract", "methodology", "conclusion"]:
         if not sections.get(s, "").strip():
             warnings.append(s)
     ```
   - On success, returns:
     ```python
     {
         "filename": file.filename,
         "sections": sections,
         "section_count": len([v for v in sections.values() if v.strip()]),
         "warnings": warnings  # list of section names not detected
     }
     ```
   - Cleans up temp file in `finally` block
7. **`if __name__ == "__main__":`** block with `uvicorn.run(app, host="0.0.0.0", port=8000)`

**Note:** Phase 1 returns only sections JSON. AI analysis (Person 2) and citation checking (Person 3) will be wired into main.py in later phases.
</action>

<acceptance_criteria>
- `main.py` contains `from fastapi import FastAPI, UploadFile, File`
- `main.py` contains `load_dotenv()`
- `main.py` contains `CORSMiddleware` with `allow_origins=["*"]`
- `main.py` contains `@app.get("/")` health check returning `{"status": "ResearchSense API is running"}`
- `main.py` contains `@app.post("/analyze")` endpoint
- `main.py` validates `.pdf` extension and returns 400 for non-PDF
- `main.py` returns a **soft warning** (not a hard rejection) if key sections are missing — analysis still proceeds
- `main.py` returns sections dict on success with keys: `filename`, `sections`, `section_count`, `warnings`
- `main.py` cleans up temp file in `finally` block
- Running `uvicorn main:app --reload` starts the server on port 8000
- `GET http://localhost:8000/` returns `{"status": "ResearchSense API is running"}`
</acceptance_criteria>

---

### Task 3: PDF Text Extraction (pdf_parser.py)

<read_first>
- ResearchSense_Research.md (Section 4 — PDF Parsing PyMuPDF)
- .planning/phases/01-environment-pdf-parser/01-CONTEXT.md (Decisions D-01, D-02, D-03)
</read_first>

<action>
Create `pdf_parser.py` with:

1. **`extract_text(pdf_path: str) -> str`** function:
   - Use **basic PyMuPDF `get_text()`** — simple, no additional dependencies:
     ```python
     import pymupdf
     def extract_text(pdf_path: str) -> str:
         """Extract plain text from a PDF file using PyMuPDF."""
         doc = pymupdf.open(pdf_path)
         text = ""
         for page in doc:
             text += page.get_text()
         doc.close()
         return text
     ```
   - **No pymupdf4llm** — not needed for MVP
   - **No OCR** — text-based PDFs only
   - If extracted text (stripped) is less than 100 characters, raise `ValueError("Could not extract text from this PDF. Please ensure it is a text-based PDF.")`
   - Return the extracted text string
</action>

<acceptance_criteria>
- `pdf_parser.py` contains `def extract_text(pdf_path: str) -> str`
- `pdf_parser.py` imports `pymupdf` and uses `get_text()` — **no pymupdf4llm import**
- `pdf_parser.py` raises `ValueError` when extracted text < 100 chars
- `pdf_parser.py` does NOT import or use tesseract/OCR
- Calling `extract_text("path/to/valid.pdf")` returns a non-empty string
</acceptance_criteria>

---

### Task 4: Regex-Only Section Detection (section_detector.py)

<read_first>
- ResearchSense_Research.md (Section 5 — Section Detection)
- .planning/phases/01-environment-pdf-parser/01-CONTEXT.md (Decisions D-04, D-05, D-06, D-07)
</read_first>

<action>
Create `section_detector.py` with:

1. **`SECTION_PATTERNS` dict** — regex patterns for each section (from ResearchSense_Research.md §5):
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

2. **`detect_sections(text: str) -> dict`** function — **regex only, no Gemini**:
   - Splits text by lines
   - Iterates through lines, matching against `SECTION_PATTERNS` (case-insensitive)
   - When a section header is found, all subsequent lines go to that section until the next header
   - Returns dict with all section keys — empty string `""` for any section not found
   - **No Gemini fallback** — if regex finds 0 sections, return the empty dict as-is

The returned dict format (must match interface contract from TEAM_SUMMARY.md):
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
</action>

<acceptance_criteria>
- `section_detector.py` contains `SECTION_PATTERNS` dict with patterns for all 8 section types
- `section_detector.py` contains `def detect_sections(text: str) -> dict` as the **only** public function
- **No `detect_sections_gemini` function** — Gemini fallback is not implemented
- Regex detection correctly identifies sections from headings like `"1. Introduction"`, `"Abstract"`, `"3. Methodology"`
- Missing sections return empty string `""` — not an error
- Returned dict always has keys: `abstract`, `introduction`, `methodology`, `results`, `discussion`, `conclusion`, `references`
- Each value is a string (empty `""` if section not found)
</acceptance_criteria>

---

## Verification

### Must-Haves (derived from Phase 1 goal)
1. ✓ FastAPI starts and accepts PDF upload on `/analyze`
2. ✓ Basic PyMuPDF `get_text()` extracts text from a real PDF
3. ✓ Regex-only section detection splits text into sections dict
4. ✓ JSON response returns identified sections + warnings list
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
