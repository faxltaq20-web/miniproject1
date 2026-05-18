# ResearchSense — Code Explanation Guide

This file explains each Python file in the project in plain language.
New files will be added here as they are built.

---

## Table of Contents

- [main.py — The API Server](#mainpy--the-api-server)
- [pdf_parser.py — PDF Text Extractor](#pdf_parserpy--pdf-text-extractor)
- [section_detector.py — Academic Section Splitter](#section_detectorpy--academic-section-splitter)

---

## main.py — The API Server

**File:** `main.py`  
**Role:** The entry point of the entire backend. It is the "manager" — it receives the uploaded PDF from the user, hands it off to the right modules, and sends back the final response.

---

### What it does, step by step

When a user uploads a research paper PDF, `main.py` runs through this exact sequence:

```
1. Is the file actually a PDF?
        ↓ No  → return error (400)
        ↓ Yes
2. Save it temporarily to disk
        ↓
3. Extract the text (hands off to pdf_parser.py)
        ↓ Scanned/empty PDF? → return error (422)
        ↓ Text extracted OK
4. Detect sections (hands off to section_detector.py)
        ↓
5. Check for missing key sections → generate soft warnings
        ↓
6. Return the result as JSON
        ↓
7. Delete the temporary file (always, even if something went wrong)
```

---

### Line-by-line breakdown

#### Imports (lines 1–6)

```python
import os
import tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
```

| Import | Why it's needed |
|---|---|
| `os` | Used to delete the temp file after analysis |
| `tempfile` | Used to save the uploaded PDF to a temporary location on disk |
| `FastAPI` | The web framework — creates the API server |
| `UploadFile`, `File` | FastAPI tools that handle file uploads from the frontend |
| `CORSMiddleware` | Allows the browser frontend (on a different port) to call this API |
| `JSONResponse` | Lets us return error responses with custom HTTP status codes |
| `load_dotenv` | Reads your `.env` file so the app can access your API keys |

---

#### Loading environment variables (line 9)

```python
load_dotenv()
```

This reads the `.env` file you have in the project root and loads things like `GEMINI_API_KEY` and `GEMINI_MODEL` into the environment. No secrets are hardcoded in the code — they all come from `.env`.

---

#### Importing pipeline modules (lines 12–13)

```python
import pdf_parser
import section_detector
```

These are the other Python files in the project. `main.py` calls their functions as part of the pipeline. Person 2's `gemini_analyzer.py` and Person 3's `citation_checker.py` will be added here in later phases.

---

#### Creating the FastAPI app (line 15)

```python
app = FastAPI(title="ResearchSense API", version="1.0.0")
```

This creates the web server application. The `title` and `version` show up in the auto-generated API docs at `http://localhost:8000/docs`.

---

#### CORS middleware (lines 18–23)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Browsers block requests between different origins (e.g. your frontend on port 5500 calling the backend on port 8000) unless the server explicitly allows it. This middleware opens up the API to all origins — fine for a university demo, but you'd restrict it in production.

---

#### Health check endpoint — `GET /` (lines 25–28)

```python
@app.get("/")
async def root():
    return {"status": "ResearchSense API is running"}
```

A simple ping endpoint. When you visit `http://localhost:8000/` in the browser or run `curl http://localhost:8000/`, it should return:

```json
{"status": "ResearchSense API is running"}
```

Useful to confirm the server is up before testing the full pipeline.

---

#### Main analyze endpoint — `POST /analyze` (lines 30–87)

This is the core of the entire backend. Here's each part explained:

**Step 1 — File type validation (lines 38–42)**

```python
if not file.filename.lower().endswith(".pdf"):
    return JSONResponse(
        status_code=400,
        content={"error": "Only PDF files are accepted"}
    )
```

If the uploaded file is not a `.pdf`, the server immediately rejects it with a `400 Bad Request` error. The `.lower()` ensures `.PDF` and `.Pdf` also pass.

---

**Step 2 — Save to a temporary file (lines 45–50)**

```python
tmp_file_path = ""
with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
    content = await file.read()
    tmp_file.write(content)
    tmp_file_path = tmp_file.name
```

The uploaded PDF arrives as a stream of bytes in memory. We can't process it directly — PyMuPDF needs a real file path on disk. So we:
1. Create a temporary file with a `.pdf` extension
2. Write the uploaded bytes into it
3. Remember the path (`tmp_file_path`) so we can delete it later

`delete=False` means the file isn't automatically deleted when we close it — we handle deletion ourselves in the `finally` block.

---

**Step 3 — Extract text (lines 52–62)**

```python
try:
    text = pdf_parser.extract_text(tmp_file_path)
except ValueError:
    return JSONResponse(
        status_code=422,
        content={
            "error": "Text extraction failed",
            "message": "Could not extract text from this PDF. Please ensure it is a text-based PDF."
        }
    )
```

We hand the temp file path to `pdf_parser.extract_text()`. If the PDF is scanned (image-only) or empty, `pdf_parser` raises a `ValueError`. We catch it and return a `422 Unprocessable Entity` error with a helpful message.

---

**Step 4 — Detect sections (line 65)**

```python
sections = section_detector.detect_sections(text)
```

Passes the extracted text to `section_detector.py`, which uses regex to split it into a dictionary of academic sections (abstract, introduction, methodology, etc.).

---

**Step 5 — Generate soft warnings (lines 68–71)**

```python
warnings = []
for s in ["abstract", "methodology", "conclusion"]:
    if not sections.get(s, "").strip():
        warnings.append(s)
```

We check the three most critical sections. If any are missing (empty string), we add them to a `warnings` list. **The analysis is NOT blocked** — it continues regardless. This is a "soft" warning, not a hard rejection.

---

**Step 6 — Return the response (lines 74–79)**

```python
return {
    "filename": file.filename,
    "sections": sections,
    "section_count": len([v for v in sections.values() if v.strip()]),
    "warnings": warnings
}
```

| Field | What it contains |
|---|---|
| `filename` | Original name of the uploaded file |
| `sections` | Dict of section name → extracted text |
| `section_count` | Number of sections that actually had content (not empty) |
| `warnings` | List of section names that were missing (empty list if all found) |

---

**Step 7 — Cleanup (lines 81–87)**

```python
finally:
    if tmp_file_path and os.path.exists(tmp_file_path):
        try:
            os.remove(tmp_file_path)
        except Exception:
            pass
```

The `finally` block runs **no matter what** — even if an error occurred earlier. This guarantees the temp file is always deleted from disk. We never permanently store uploaded PDFs.

---

#### Starting the server directly (lines 89–91)

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This lets you run `python main.py` directly. In practice you'll use `uvicorn main:app --reload` instead, which gives you hot-reload during development.

---

### How to run it

```bash
# Development mode (auto-restarts when you save a file)
uvicorn main:app --reload

# Then open in browser:
# http://localhost:8000/       ← health check
# http://localhost:8000/docs   ← interactive API docs (auto-generated by FastAPI)
```

---

---

## pdf_parser.py — PDF Text Extractor

**File:** `pdf_parser.py`  
**Role:** A single-responsibility module. Its only job is to open a PDF file and return all its text as a plain Python string. It has one function and 17 lines.

---

### What it does

```
Given a path to a PDF file on disk
        ↓
Open the PDF with PyMuPDF
        ↓
Loop through every page → extract text → join it together
        ↓
Is the total text < 100 characters?
        ↓ Yes → raise ValueError (scanned/image PDF, can't use it)
        ↓ No  → return the full text string
```

---

### Full file with explanation

```python
import pymupdf
```

`pymupdf` is the Python library for reading PDF files. It's the package installed by `pip install pymupdf`. (Confusingly, the package on PyPI is called `pymupdf` but it used to be called `fitz` — you may see `import fitz` in older code. We use the newer `import pymupdf` name.)

---

```python
def extract_text(pdf_path: str) -> str:
```

- Takes one argument: `pdf_path` — the file path string to the PDF on disk
- Returns one thing: `str` — all the text from the PDF joined together
- The `: str` and `-> str` are Python **type hints** — they're documentation that tells other developers (and your IDE) what types to expect. They don't change how the code runs.

---

```python
doc = pymupdf.open(pdf_path)
```

Opens the PDF file. `doc` is now a PyMuPDF document object — think of it like a list of pages you can loop through.

---

```python
text = ""
for page in doc:
    text += page.get_text()
doc.close()
```

- Starts with an empty string
- Loops through every page in the document
- `page.get_text()` extracts all the raw text from that page and appends it
- After the loop, `text` contains the entire document's content as one long string
- `doc.close()` frees the file from memory — important to always close files you open

> **Why basic `get_text()` and not something fancier?**  
> There's a more advanced library called `pymupdf4llm` that converts PDFs to Markdown format, which is better for AI processing. We deliberately chose NOT to use it — it adds complexity and dependencies for an MVP. The plain text from `get_text()` is good enough for our regex section detector and Gemini prompts.

---

```python
if len(text.strip()) < 100:
    raise ValueError(
        "Could not extract text from this PDF. Please ensure it is a text-based PDF."
    )
```

- `text.strip()` removes leading/trailing whitespace before measuring length
- If the total extracted text is shorter than 100 characters, the PDF is almost certainly a **scanned document** (just images, no embedded text) or completely empty
- We raise a `ValueError` with a clear message — `main.py` catches this and returns a 422 error to the user
- 100 chars is a practical threshold — even a 1-page abstract would produce hundreds of characters

---

```python
return text
```

If everything went fine, return the full extracted text string. `main.py` receives this and passes it to `section_detector.py`.

---

### Why it's a separate file

`pdf_parser.py` is kept separate from `main.py` deliberately:

1. **Team ownership** — Person 1 owns this file. If the extraction logic needs changing, there's one clear place to edit it.
2. **Testability** — You can test `extract_text()` in isolation without starting the whole server.
3. **Single responsibility** — This file does exactly one thing. `main.py` orchestrates; `pdf_parser.py` extracts.

---

### Quick test (without starting the server)

```python
# Run in a Python shell from the project folder
import pdf_parser
text = pdf_parser.extract_text("some_paper.pdf")
print(text[:500])  # print first 500 characters
```

---

---

## section_detector.py — Academic Section Splitter

**File:** `section_detector.py`  
**Role:** Takes the raw text string from `pdf_parser.py` and splits it into a labelled dictionary of academic sections — abstract, introduction, methodology, results, discussion, conclusion, references. Uses pure regex, no AI.

---

### What it does

```
Receive full paper text (one big string)
        ↓
Split into individual lines
        ↓
For each line: does it look like a section heading?
        ↓ Yes → switch "current section" to that section name
        ↓ No  → add the line to whichever section is currently active
        ↓
Return a dict: { "abstract": "...", "introduction": "...", ... }
        ↓
Any section not found → empty string ""
```

---

### Part 1 — SECTION_PATTERNS (lines 3–12)

```python
SECTION_PATTERNS = {
    "abstract":         r"\b(abstract)\b",
    "introduction":     r"\b(1\.?\s*introduction|introduction)\b",
    "literature_review":r"\b(2\.?\s*(literature review|related work|background))\b",
    "methodology":      r"\b(\d\.?\s*(methodology|methods|method|approach|experimental setup))\b",
    "results":          r"\b(\d\.?\s*(results|findings|experiments|evaluation))\b",
    "discussion":       r"\b(\d\.?\s*(discussion|analysis))\b",
    "conclusion":       r"\b(\d\.?\s*(conclusion|conclusions|summary|closing remarks))\b",
    "references":       r"\b(references|bibliography|works cited)\b"
}
```

This is a dictionary of **regex patterns** — one for each section. Each key is the section name, and the value is the regex that matches that section's heading in the paper.

**Reading the regex patterns:**

| Symbol | Meaning |
|---|---|
| `\b` | Word boundary — ensures we match a whole word, not part of a word (e.g. "abstract" but not "abstracts") |
| `( )` | Group — matches any one of the alternatives inside |
| `\|` (pipe) | OR — match either the left or right side |
| `\.?` | Optional dot — matches both `1.` and `1` |
| `\s*` | Zero or more spaces — handles `1. Introduction` and `1.Introduction` |
| `\d` | Any single digit — matches the numbered prefix like `3.` in `3. Methodology` |

**What each pattern actually matches in a real paper:**

| Section | Matched headings |
|---|---|
| `abstract` | `Abstract` |
| `introduction` | `Introduction`, `1. Introduction`, `1 Introduction` |
| `literature_review` | `2. Literature Review`, `Related Work`, `Background` |
| `methodology` | `3. Methodology`, `Methods`, `Approach`, `Experimental Setup` |
| `results` | `4. Results`, `Findings`, `Experiments`, `Evaluation` |
| `discussion` | `5. Discussion`, `Analysis` |
| `conclusion` | `6. Conclusion`, `Conclusions`, `Summary`, `Closing Remarks` |
| `references` | `References`, `Bibliography`, `Works Cited` |

> **Why regex and not AI?**  
> Academic papers follow predictable heading patterns. Regex covers the standard formats reliably and instantly — no API call, no token cost, no network dependency. Gemini fallback was considered but removed from the MVP to save API quota and keep the pipeline fast.

---

### Part 2 — detect_sections function (lines 14–58)

#### Initialising the output dictionary (lines 19–32)

```python
lines = text.splitlines()

sections = {
    "abstract": "",
    "introduction": "",
    "methodology": "",
    "results": "",
    "discussion": "",
    "conclusion": "",
    "references": ""
}
sections["literature_review"] = ""
```

- `text.splitlines()` breaks the big text string into a list of individual lines — easier to process one at a time
- The `sections` dict is pre-filled with all 7 required keys set to empty strings `""`
- This guarantees that even if a section is never found, the key still exists — so `sections["methodology"]` never causes a `KeyError`
- `literature_review` is added separately as a bonus 8th key — it's not in the 7-key interface contract but is tracked if the paper has it

---

#### The main loop (lines 36–52)

```python
current_section = None

for line in lines:
    line_lower = line.strip().lower()

    matched_section = None
    for section_name, pattern in SECTION_PATTERNS.items():
        if re.search(pattern, line_lower):
            matched_section = section_name
            break

    if matched_section:
        current_section = matched_section
        sections[current_section] += line + "\n"
    elif current_section:
        sections[current_section] += line + "\n"
```

Step by step:

1. `current_section = None` — we start with no active section (text before any heading is discarded)
2. For each line, `line.strip().lower()` — trim whitespace and lowercase it so `"3. METHODOLOGY"` matches the same as `"3. methodology"`
3. Try every pattern in `SECTION_PATTERNS` using `re.search()` — if any matches, that's the new active section
4. **If a heading matched:** switch `current_section` to that section name and add the heading line itself to the section content
5. **If no heading matched AND we're inside a section:** add the line to the current section's accumulated text
6. **If no heading matched AND we haven't entered any section yet:** the line is silently skipped (e.g. page numbers, journal headers at the top of the paper)

**Visual example:**
```
Line: "Abstract"            → matched: abstract → current_section = "abstract"
Line: "This paper studies…" → no match, current=abstract → added to abstract
Line: "1. Introduction"     → matched: introduction → current_section = "introduction"
Line: "Machine learning…"   → no match, current=introduction → added to introduction
```

---

#### Cleanup (lines 54–56)

```python
for k in sections:
    sections[k] = sections[k].strip()
```

Each section's accumulated text may have leading/trailing newlines from the loop. This trims them so downstream code gets clean strings.

---

#### Return (line 58)

```python
return sections
```

The complete dictionary is returned to `main.py`, which then:
- Counts how many sections have content (`section_count`)
- Checks if `abstract`, `methodology`, `conclusion` are empty (soft warnings)
- Includes the full dict in the JSON response

---

### The interface contract

The 7 keys that `section_detector.py` guarantees to always return (even as empty strings):

```python
{
    "abstract":      str,   # empty string if not found
    "introduction":  str,
    "methodology":   str,
    "results":       str,
    "discussion":    str,
    "conclusion":    str,
    "references":    str
}
```

Person 2 (`gemini_analyzer.py`) and Person 3 (`citation_checker.py`) both consume this dict. They can safely access any key without checking if it exists first.

> **Bonus key:** `literature_review` may also appear in the dict if the paper has that section — but it's not part of the 7-key contract and downstream code should not rely on it.

---

### Quick test (without starting the server)

```python
# Run in a Python shell from the project folder
import section_detector

sample = """
Abstract
This paper studies X.

1. Introduction
Introduction text here.

3. Methodology
We used method Y.

References
[1] Smith 2020
"""

result = section_detector.detect_sections(sample)
for section, text in result.items():
    status = 'FOUND' if text else 'EMPTY'
    print(f"{section}: {status}")
```

Expected output:
```
abstract: FOUND
introduction: FOUND
methodology: FOUND
results: EMPTY
discussion: EMPTY
conclusion: EMPTY
references: FOUND
literature_review: EMPTY
```

---

*Last updated: 2026-05-18 — covers main.py, pdf_parser.py, section_detector.py (Phase 1, Plan 01)*  
*Next to be added: gemini_analyzer.py, scoring.py, citation_checker.py, report_generator.py*
