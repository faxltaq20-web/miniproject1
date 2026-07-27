# ResearchSense — Detailed System Architecture & Workflow Blueprint

This document provides a low-level, comprehensive explanation of the **ResearchSense** system architecture and the step-by-step document execution pipeline.

---

## 1. System Architecture Overview

ResearchSense is structured around a decoupled model where a **FastAPI backend** manages resource-intensive tasks (PDF parsing, semantic segmentation, external telemetry queries, LLM integration, and PDF report assembly), and a **vanilla HTML/CSS/JS frontend SPA** coordinates the user interface state and renders dynamic dashboard panels.

```
                  +-----------------------------------+
                  |           User (Browser)          |
                  +-----------------+-----------------+
                                    |
                    1. Upload PDF   |  10. Return PDF Report
                                    v
                  +-----------------+-----------------+
                  |      Web Dashboard SPA (app.js)   |
                  +-----------------+-----------------+
                                    |
              2. POST /analyze      |  9. POST /report
                                    v
    ==================================================================
                       BACKEND ENGINE (main.py)
    ==================================================================
                                    |
                                    +----> 3. pdf_parser.py
                                    |      (PyMuPDF4LLM Text & Links)
                                    |
                                    +----> 4. section_detector.py
                                    |      (Tier 1 Regex / Tier 2 LLM)
                                    |
                                    +----> 5. text_compressor.py
                                    |      (Light / Aggressive prep)
                                    |
                     +--------------+--------------+
                     | [Parallel asyncio.gather]   |
                     v                             v
           6. gemini_analyzer.py          7. citation_checker.py
           (4-Layer LLM evaluation)       (CrossRef, SS, ArXiv lookup)
                     +--------------+--------------+
                                    |
                                    v
                           8. scoring.py
                           (Discipline-adaptive weight)
                                    |
                                    v
                           report_generator.py
                           (PLATYPUS PDF compiler)
    ==================================================================
```

---

## 2. End-to-End Workflow: Step-by-Step

### Step 1: Client Upload (`app.js`)
* **Trigger:** The user drag-and-drops or browses a `.pdf` file in the `#dropZone` component.
* **Logic:** The frontend validates that the file has a `.pdf` suffix. If valid, the file is wrapped in a `FormData` object and dispatched via an asynchronous `fetch` call to the `POST /analyze` endpoint. The simulated stepper is activated in the UI.

### Step 2: Input Validation & Streaming (`main.py`)
* **Trigger:** FastAPI receives the multipart request at `/analyze`.
* **Logic:**
  1. The API calls `gemini_analyzer.check_api_health()` to ensure at least one Gemini key is active; if all are dead, it aborts with an HTTP 503.
  2. It validates the file extension.
  3. The PDF is streamed to a temporary file in 1 MB chunks. If the cumulative payload exceeds the `MAX_UPLOAD_BYTES` threshold (30 MB default), the upload is immediately aborted with an HTTP 413, protecting server memory.

### Step 3: Document Extraction (`pdf_parser.py`)
* **Trigger:** The temporary PDF path is passed to `pdf_parser.extract_text()`.
* **Logic:**
  1. **Primary Stage:** The parser runs `pymupdf4llm.to_markdown()` to extract the document text in clean Markdown, which helps retain heading styles.
  2. **Fallback Stage:** If primary parsing fails or outputs fewer than 100 characters, it falls back to raw text extraction via plain PyMuPDF (`fitz` module), utilizing blocks sorting (`sort=True`) to correctly serialize two-column layouts.
  3. **Link Annotation Extraction:** Concurrently, `pdf_parser.extract_hyperlink_dois()` scans the document's link annotations for hidden publisher-embedded DOIs that aren't visible as text.

### Step 4: Academic Section Segmentation (`section_detector.py`)
* **Trigger:** Extracted text is fed into the section detector.
* **Logic:**
  1. **Tier 1 (Keywords):** Lines are scanned for heading shapes (e.g. ALL CAPS or Markdown headers) and compared against a list of pre-defined academic section keywords.
  2. **Tier 2 (LLM Fallback):** If Tier 1 fails to identify at least four sections, the segmenter extracts all heading lines (capped at 40) and queries Gemini with `map_headings()` to map each heading to standard section keys.
  3. Section text is accumulated, stop keywords (like `appendix` or `acknowledgements`) terminate scanning, and a deterministic length-aware confidence percentage is computed for each parsed section.

### Step 5: Parallel Pipeline Dispatch (`main.py`)
* **Trigger:** The FastAPI backend dispatches two distinct processing threads in parallel using `asyncio.gather()`.
* **Logic:**
  * **Thread A (gemini_analyzer.py):**
    1. Pre-processes the sections dict through `text_compressor.py` (stripping whitespace, URL noise, citations, and boilerplate sentences).
    2. Shields the critical `methodology` section from compression.
    3. Assembles the text (capped at 400,000 characters) and checks the local `cache/` directory using a SHA-256 hash. If there is a cache hit, it returns the result immediately.
    4. On a cache miss, it calls Gemini to analyze the paper across 4 layers (Structure, Clarity, Methodology, Evidence) and classify the discipline in a single API call using structured JSON schemas.
    5. Calibrates raw scores (stretching the narrow 6–8 band around 7.0 by 1.5) and writes the result to the cache.
  * **Thread B (citation_checker.py):**
    1. Sweeps the reference section for DOIs and merges them with hyperlink-based DOIs (capped at 20).
    2. Concurrently queries the CrossRef API using a thread pool.
    3. For unverified references, it falls back to querying Semantic Scholar with the parsed titles (capped at 5 fallback lookups).
    4. Evaluates reference recency compared to the paper's own publication year, identifies duplicate listings, and boosts CS papers with valid ArXiv preprint IDs.

### Step 6: Discipline-Adaptive Scoring (`scoring.py`)
* **Trigger:** The backend receives the parallel outputs and merges the citation score into the score sheet.
* **Logic:** The scoring engine maps the 5 layer scores to the specific weights defined for the paper's discipline (e.g., mathematics weights evidence heaviest; humanities weights clarity heaviest). It calculates the final 0–100 score and assigns a letter grade (A to F).

### Step 7: Verdict Synthesis (`gemini_analyzer.py`)
* **Trigger:** Final scores and details are passed to `generate_verdict()`.
* **Logic:** Gemini is prompted to write a concise 2-3 sentence overview assessing overall paper quality, focusing on the two lowest-scoring dimensions and their issues. If all API keys are exhausted, the engine falls back to pre-written, grade-appropriate template strings.

### Step 8: Dashboard Rendering (`app.js`)
* **Trigger:** The client receives the unified JSON payload.
* **Logic:**
  1. The fake stepper sequence is stopped and marked as complete.
  2. The circular SVG gauge is animated using a CSS transition.
  3. Detected section badges are populated (red if missing).
  4. Accordion cards are generated for all 5 layers, rendering issues in red and actionable fixes in green.
  5. The references list is populated with tooltips showing check statuses.

### Step 9: Report Synthesis (`report_generator.py`)
* **Trigger:** The user clicks the "Download PDF Review Report" action button in the dashboard, triggering a `POST /report` request.
* **Logic:**
  1. The backend consumes the raw dashboard JSON body (no re-calculation occurs).
  2. It translates the scores to earned vs. maximum marks based on discipline weights.
  3. report_generator compiles the PLATYPUS document: runs canvas drawing for the navy cover page, and generates flowable paragraphs, tables, and progress bars.
  4. The PDF is saved to an in-memory `BytesIO` buffer and streamed back to the client, triggering an immediate download action in the browser.

---

## 3. High-Resolution Workflow Diagram

The step-by-step visual representation of this workflow can be viewed here:

* **PNG Format:** [workflow_details.png](file:///c:/Users/mohdf/mini%20project/docs/workflow_details.png)
* **SVG Format:** [workflow_details.svg](file:///c:/Users/mohdf/mini%20project/docs/workflow_details.svg)
