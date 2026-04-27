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

Person 1 builds the entire backend foundation for ResearchSense: project scaffolding, FastAPI skeleton with the `/analyze` endpoint, PDF text extraction using pymupdf4llm, and section detection with regex + Gemini fallback. This is the core pipeline that all other team members will consume.

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
pymupdf4llm
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
GEMINI_MODEL_PRIMARY=gemini-2.5-flash
GEMINI_MODEL_FALLBACK=gemini-2.5-flash-lite
CONTACT_EMAIL=your_email@example.com
```

Verify `.gitignore` already contains `.env` — if not, add it.

Create a personal `.env` file (not committed) with your actual `GEMINI_API_KEY`.
</action>

<acceptance_criteria>
- `requirements.txt` exists and contains all 10 packages listed above
- `.env.example` exists and contains `GEMINI_API_KEY=`, `GEMINI_MODEL_PRIMARY=`, `GEMINI_MODEL_FALLBACK=`, `CONTACT_EMAIL=`
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
   - Checks minimum sections (Abstract + Methodology + Conclusion) — if any missing, returns 422 with formal rejection:
     ```python
     {
         "error": "Structural validation failed",
         "missing_sections": ["methodology"],
         "message": "Structural validation failed: The following required sections were not detected: [Methodology]. Papers must contain Abstract, Methodology, and Conclusion to proceed with analysis.",
         "note": "Please ensure your paper follows standard academic structure. A sample format guide will be available in a future update."
     }
     ```
   - On success, returns sections JSON:
     ```python
     {
         "filename": file.filename,
         "sections": sections,
         "section_count": len([v for v in sections.values() if v.strip()])
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
- `main.py` checks for Abstract, Methodology, Conclusion — returns 422 with `"Structural validation failed"` if any missing
- `main.py` returns sections dict on success with keys: `filename`, `sections`, `section_count`
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
   - **Primary method:** Use `pymupdf4llm.to_markdown(pdf_path)` — this preserves heading structure for better section detection
   - **Fallback:** If pymupdf4llm raises any exception, fall back to basic PyMuPDF extraction:
     ```python
     import pymupdf
     doc = pymupdf.open(pdf_path)
     text = ""
     for page in doc:
         text += page.get_text()
     doc.close()
     return text
     ```
   - **Scanned PDF detection:** After extraction, if the resulting text (stripped) is less than 100 characters, raise a `ValueError` with message: `"This appears to be a scanned PDF. Please upload a text-based PDF."`
   - Return the extracted text string

2. **No OCR** — per decision D-03, scanned PDFs are rejected, not OCR'd
</action>

<acceptance_criteria>
- `pdf_parser.py` contains `def extract_text(pdf_path: str) -> str`
- `pdf_parser.py` imports `pymupdf4llm` and uses `to_markdown()` as primary extraction
- `pdf_parser.py` imports `pymupdf` and uses `get_text()` as fallback in a `try/except` block
- `pdf_parser.py` raises `ValueError("This appears to be a scanned PDF")` when extracted text < 100 chars
- `pdf_parser.py` does NOT import or use tesseract/OCR
- Calling `extract_text("path/to/valid.pdf")` returns a non-empty string
</acceptance_criteria>

---

### Task 4: Section Detection with Gemini Fallback (section_detector.py)

<read_first>
- ResearchSense_Research.md (Section 5 — Section Detection)
- .planning/phases/01-environment-pdf-parser/01-CONTEXT.md (Decisions D-04, D-05, D-06, D-07, D-12, D-13)
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

2. **`detect_sections_regex(text: str) -> dict`** function:
   - Splits text by lines
   - Iterates through lines, matching against `SECTION_PATTERNS`
   - When a section header is found, all subsequent lines go to that section until the next header
   - Returns dict with keys: `abstract`, `introduction`, `literature_review`, `methodology`, `results`, `discussion`, `conclusion`, `references` — each value is the section text (empty string `""` if not found)

3. **`detect_sections_gemini(text: str) -> dict`** function:
   - Imports `google.generativeai as genai` and `os`
   - Loads model from env: `os.getenv("GEMINI_MODEL_PRIMARY", "gemini-2.5-flash")`
   - Sends prompt asking Gemini to split text into sections (first 8000 chars)
   - Parses JSON response
   - On failure/invalid JSON: retries once with stricter prompt suffix: `"Return ONLY valid JSON. No markdown code blocks. No explanatory text."`
   - On second failure: returns empty sections dict
   - Implements primary→fallback model chain per D-12

4. **`detect_sections(text: str) -> dict`** function (main entry point):
   - Calls `detect_sections_regex(text)` first
   - Counts non-empty sections: `found = len([v for v in sections.values() if v.strip()])`
   - If `found < 3`: calls `detect_sections_gemini(text)` as fallback
   - Returns the final sections dict

The returned dict format must match the interface contract from TEAM_SUMMARY.md:
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
- `section_detector.py` contains `def detect_sections_regex(text: str) -> dict`
- `section_detector.py` contains `def detect_sections_gemini(text: str) -> dict`
- `section_detector.py` contains `def detect_sections(text: str) -> dict` as the main entry point
- Regex detection correctly identifies sections from headings like `"1. Introduction"`, `"Abstract"`, `"3. Methodology"`
- Gemini fallback triggers only when `len(found_sections) < 3`
- Gemini fallback uses `GEMINI_MODEL_PRIMARY` env var, with `GEMINI_MODEL_FALLBACK` as secondary
- Invalid JSON from Gemini triggers one retry with stricter prompt
- Returned dict always has keys: `abstract`, `introduction`, `methodology`, `results`, `discussion`, `conclusion`, `references`
- Each value is a string (empty `""` if section not found)
</acceptance_criteria>

---

## Verification

### Must-Haves (derived from Phase 1 goal)
1. ✓ FastAPI starts and accepts PDF upload on `/analyze`
2. ✓ pymupdf4llm extracts text from a real PDF
3. ✓ Section detection splits text using regex (with Gemini fallback)
4. ✓ JSON response returns identified sections
5. ✓ Missing required sections (Abstract/Methodology/Conclusion) return formal rejection
6. ✓ Scanned PDFs are rejected gracefully
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
