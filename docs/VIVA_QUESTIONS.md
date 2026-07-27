# ResearchSense — Project Presentation & Viva Q&A Guide

This guide contains potential viva questions that examiners or evaluators might ask during the project presentation, organized by category. Each answer is kept to **1 to 2 sentences** to remain concise, clear, and direct.

---

## 1. General & Architecture Questions

### Q1: What is the core objective of the ResearchSense project?
ResearchSense is an automated academic paper quality analysis tool that extracts text from a PDF, evaluates it across 5 qualitative layers using LLMs, verifies reference credibility against external databases, and generates a detailed visual report.

### Q2: Why did you choose a FastAPI backend instead of Flask or Django?
FastAPI was selected for its high performance, native asynchronous (`async/await`) support, which allows concurrent processing of parallel LLM calls and citation checks, and its automatic generation of OpenAPI documentation.

### Q3: Explain the high-level architecture of this application.
It is a decoupled client-server architecture where a FastAPI backend orchestrates document parsing, AI evaluation, and citation verification, while a lightweight, glassmorphic Single Page Application (SPA) frontend handles user interaction and displays results.

### Q4: How are the backend and frontend integrated?
The FastAPI backend serves the frontend statically through `StaticFiles`. The client-side code (`app.js`) interacts with the backend endpoints via same-origin asynchronous `fetch` requests, eliminating Cross-Origin Resource Sharing (CORS) issues in production.

### Q5: What is the sequence of the document analysis pipeline?
When a PDF is uploaded, the backend extracts the text, segments it into academic sections, runs the Gemini LLM qualitative analysis and external citation lookups in parallel, calculates a weighted discipline-adaptive score, and returns the unified JSON dashboard payload.

### Q6: What is the role of `asyncio.to_thread` in this project?
Since Python is single-threaded and the Gemini SDK / citation APIs are blocking I/O operations, we wrap them in `asyncio.to_thread` to execute them in separate worker threads, preventing the FastAPI event loop from freezing.

### Q7: How does this project handle thread safety or concurrent file uploads?
FastAPI creates a separate worker thread or thread-pool executor for synchronous route handlers, and by streaming uploads into randomized temporary files (`NamedTemporaryFile`), we isolate each request's state.

---

## 2. PDF Extraction & Section Detection

### Q8: How does the system extract text from the uploaded PDF?
It utilizes a dual-stage strategy: it first tries to extract text into structured Markdown using `pymupdf4llm` to preserve layout hierarchy, and falls back to plain PyMuPDF (`fitz` module) with layout sorting enabled if the primary extraction fails.

### Q9: How does the system detect reference DOIs that are not printed as text in the bibliography?
The system parses the PDF page's clickable link annotations using `page.get_links()` to extract DOIs embedded as active URLs, which are commonly used by publishers like IEEE and Springer but omitted from the visible text.

### Q10: What happens if a user uploads a scanned image-only PDF?
The system checks if the extracted text length is less than 100 characters. If so, it raises a `ValueError` which the FastAPI backend translates to a `422 Unprocessable Entity` response with a warning that the PDF is image-only.

### Q11: Explain the two-tier section detection mechanism in `section_detector.py`.
Tier 1 runs a fast, regex-based keyword scan to locate standard section boundaries (e.g. Introduction, Methodology). If Tier 1 finds fewer than four sections, Tier 2 automatically extracts all headings and queries Gemini to semantically map them to standard section keys.

### Q12: How does the system prevent bibliographical lines from being falsely identified as section headings?
It uses a regex check to ignore lines that start with reference markers like `[12]` or `1.` followed by title-case words, filtering out bibliography entries from heading detection.

### Q13: What is the significance of the `sort=True` parameter in fitz's `get_text()` function?
It tells PyMuPDF to sort text blocks by coordinates (reading order) so that double-column pages are read column-by-column rather than straight across, avoiding interleaved/corrupted text lines.

---

## 3. Generative AI Layer & Key Rotation

### Q14: How do you evaluate the quality of the paper using the LLM?
We send the parsed sections to the `gemini-2.5-flash` model using a detailed system prompt covering 4 evaluation dimensions: Structure & Sections, Clarity & Writing, Methodology Rigor, and Evidence & Claims.

### Q15: Why did you evaluate all four AI layers in a single API call instead of four separate calls?
Evaluating all layers in a single call reduces total latency from ~60 seconds to ~15 seconds and drastically saves API token usage, keeping the application well within free-tier limits.

### Q16: How does the system handle Gemini API rate limits on the free tier?
We implement a multi-key client pool in `gemini_analyzer.py` that loads up to 5 API keys from `.env`. If a key encounters a `429 Resource Exhausted` error, the client immediately rotates to the next key in the pool.

### Q17: How does the system deal with transient server overloads or 503 errors?
When the API returns a transient error (such as a 503 or overload), the backend intercepts it and performs up to 3 retries using exponential backoff (retrying after 5s, 10s, and 20s) before rotating the key.

### Q18: What is the purpose of the result caching mechanism in `gemini_analyzer.py`?
We generate a SHA-256 hash of the assembled paper text and store the calibrated Gemini analysis in the local `cache/` directory. Re-uploading the same paper loads the cached JSON instantly, requiring zero API calls and reducing latency to under a second.

### Q19: Why and how do you calibrate the raw scores returned by the LLM?
LLM scores tend to cluster in the narrow 6–8 band. We apply a linear stretch factor of 1.5 centered around 7.0 to spread these scores, making quality differences more apparent while preserving 0.0 as a "section missing" sentinel.

### Q20: How do you guarantee that the Gemini API returns a valid JSON string that Python can parse?
We configure Gemini's native JSON mode using `response_mime_type="application/json"` and attach a Pydantic-like structured schema (`RESPONSE_SCHEMA`) to the API call.

### Q21: What parameters are configured for the Gemini text generation call and why?
We set `temperature=0.0` and `top_p=0.8` to force deterministic and consistent outputs, and set `max_output_tokens=8000` to prevent the generated JSON text from being truncated.

---

## 4. Text Compression

### Q22: Why do you compress the text before sending it to the Gemini API?
Compression reduces input token usage by 30% to 65% depending on the mode, which reduces latency and allows us to fit longer papers into the Gemini context window.

### Q23: What are the differences between the `light` and `aggressive` compression modes?
`light` mode normalizes whitespace, strips inline citations (like `[1]` or `(Smith, 2020)`), and removes standard academic filler boilerplate. `aggressive` mode does all of this and additionally removes mathematical equations and formulas.

### Q24: Why is the `methodology` section shielded from text compression?
The methodology section contains dense technical detail and evidence that is critical for scoring accuracy; compressing it could cause the LLM to miss vital details and result in incorrect evaluation scores.

### Q25: How does the sentence deduplication logic in `text_compressor.py` avoid stripping duplicate sentences legitimately repeated across sections?
The sentence deduplication scope is restricted strictly to the current section text block (`within_section_only=True`), preventing it from stripping identical summary sentences repeated in the abstract or conclusion.

### Q26: What is an "evidence pointer" and why is it shielded from compression in the results section?
Evidence pointers are references to visual data (like "As shown in Figure 2"). Stripping them from results or discussion sections would break the semantic link between LLM claims and quantitative data.

---

## 5. Bibliography & Citation Telemetry

### Q27: How does the citation checker evaluate the references section?
It parses the bibliography entries and checks up to 20 unique DOIs in parallel against the CrossRef API. For references without DOIs, it falls back to querying the Semantic Scholar API with the paper title and publication year.

### Q28: What is the purpose of the ArXiv ID check?
Preprints or computer science papers often cite ArXiv IDs instead of DOIs. The system extracts these IDs and queries the public ArXiv Atom API to verify their existence, adding a score boost if they are valid.

### Q29: How is the citation score calculated if the network is throttled or external APIs are down?
If queries to CrossRef or Semantic Scholar time out, the citations are marked as "unreachable" and are excluded from the score denominator. This prevents network timeouts from unfairly lowering the user's score.

### Q30: How does the system detect duplicate references?
The duplicate detector normalizes whitespace on reference lines and compares the first 60 characters of each bibliography entry. If a matching prefix is found, it flags it as a duplicate in the dashboard and applies a small score penalty.

### Q31: How does the system check citation recency?
It heuristically extracts the publication year of the uploaded paper from the first 4000 characters. It then checks what percentage of the references were published within 3 years prior to that year and maps this ratio to a 4.0 to 10.0 scale.

### Q32: Why does Semantic Scholar title search use a year-aware matching threshold?
If the years of the reference and the query match (within ±1 year), we lower the fuzzy matching threshold to 0.5 because the matching year provides a strong co-verification signal.

### Q33: Why is the title fallback queries list capped at `MAX_TITLE_FALLBACK = 5` and how are they selected?
Capping is necessary to prevent Semantic Scholar rate limits (429 errors). We distribute these 5 slots proportionally across the entire bibliography list to get a representative sample of the paper.

---

## 6. Scoring, Grading & PDF Generation

### Q34: What is discipline-adaptive scoring and why is it used?
Different fields value different aspects of a paper; for example, a mathematics paper prioritizes evidence (proofs), while a medical paper prioritizes methodology (trials). We dynamically adjust the weights of the 5 layers based on the paper's discipline as classified by Gemini.

### Q35: How are the scores mapped to grades?
The composite weighted score (0–100) is mapped to standard academic letter grades: A (≥85), B (≥70), C (≥55), D (≥40), and F (<40).

### Q36: How is the PDF review report generated?
We use ReportLab's PLATYPUS framework. It combines canvas-level drawing for a dark, full-bleed cover page with standard flowables (tables, paragraphs, progress bars) for the structured content pages.

### Q37: How is the PDF delivered to the user without consuming server disk space?
The PDF is compiled in-memory as a `BytesIO` binary stream. It is streamed directly to the browser as an attachment, meaning no files are ever written to or stored on the server's hard drive.

### Q38: What is the difference between ReportLab's Canvas API and its PLATYPUS framework?
Canvas is a low-level graphics tool requiring exact coordinates, whereas PLATYPUS is a high-level layout manager that automatically handles page breaks, paragraph wrapping, and flowable tables.

### Q39: How does `report_generator.py` prevent XML parsing errors in ReportLab?
It runs a helper function `_sanitize()` that strips out Markdown bold markers (`**`) and escapes HTML entities (like `<`, `>`, and `&`) before formatting paragraphs.

---

## 7. Frontend SPA & Electron Desktop

### Q40: What tech stack is used on the frontend?
The frontend is built using vanilla HTML, vanilla CSS (utilizing HSL colors, CSS Grid, and custom transitions), and vanilla JavaScript (`app.js`) to keep the interface fast, responsive, and dependency-free.

### Q41: How does the frontend stepper simulate the backend progress?
The frontend runs a step-based loading screen that increments every 4.5 seconds to show visual feedback during the API call. Once the backend response returns, the timer is cleared and the stepper jumps to the dashboard view.

### Q42: How does the Electron shell wrap the web application?
Electron creates a frameless `BrowserWindow` that boots the FastAPI server as a background child process, waits for it to signal readiness, and loads the local backend URL into the desktop interface.

### Q43: How do window controls work in the desktop app if the OS titlebar is removed?
We use an Electron `preload.js` script to expose a safe, IPC-based `electronAPI` (`minimize`, `maximize`, `close`) to the frontend window. The custom HTML titlebar handles dragging via the `-webkit-app-region: drag` CSS property.

### Q44: How does the gauge animation dynamically compute its visual progress?
The SVG circle's `stroke-dashoffset` is computed in JavaScript using `circumference * (1 - score / 100)` and set as an inline style, triggering the CSS dashoffset transition.

### Q45: How does the Electron process determine where the Python executable resides?
Electron executes `resolveVenvPython()`, which resolves a platform-aware path (`venv\Scripts\python.exe` on Windows, `venv/bin/python` on POSIX) relative to the application resource root.

---

## 8. Deployment & Edge Cases

### Q46: How is the application deployed to production?
It is configured for one-click deployment on Render using a `render.yaml` manifest. The FastAPI backend runs on a single Web Service node and serves both the API endpoints and the static frontend folder.

### Q47: How does the frontend manage Render's free-tier "cold starts"?
When the app loads, `checkBackendHealth()` polls `GET /health` every 3 seconds for up to 60 seconds. It displays a visual countdown to the user while the server wakes up from its sleeping state.

### Q48: What happens if a user tries to upload a non-PDF file?
The frontend performs client-side validation on the file extension and blocks the upload. If bypassed, the backend's `/analyze` route checks the file suffix and returns a `400 Bad Request` with an error message.

### Q49: How is file locking handled when running the local pipeline script (`run_local.py`)?
If the output PDF is open (e.g., in Adobe Reader) and locked, `save_file_safely` catches the `PermissionError` and appends a version suffix (`_v1`, `_v2`) to write the file successfully.

### Q50: How are environment variables handled in the packaged Electron desktop app?
Since local desktop users don't have server environment variables, the Electron wrapper reads the local `.env` file located in the application's root folder at launch.
