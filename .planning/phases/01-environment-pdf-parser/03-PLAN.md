---
phase: 1
plan: 3
title: "Person 3 — Citations, Report & Frontend Stubs"
owner: "Person 3 (P3)"
wave: 1
depends_on: []
files_modified:
  - citation_checker.py
  - report_generator.py
  - frontend/index.html
  - frontend/style.css
  - frontend/app.js
requirements:
  - CORE-01
  - CORE-04
autonomous: true
---

# Plan 03: Person 3 — Citations, Report & Frontend Stubs

## Objective

Person 3 creates the foundation files for citation checking, report generation, and the frontend UI during Phase 1. The citation module provides real DOI regex extraction (useful immediately) plus a stub entry point for Phase 3. The report module is a stub that Phase 4 will implement. The frontend is a working upload UI that connects to Person 1's FastAPI backend.

## Owner

**Person 3 (P3)** — Citations, Report & Frontend

---

## Tasks

### Task 1: Citation Checker Stub (citation_checker.py)

<read_first>
- TEAM_SUMMARY.md (Section 3 — Person 3 Responsibilities)
- ResearchSense_Research.md (Section 7 — Semantic Scholar API, Section 8 — CrossRef API)
</read_first>

<action>
Create `citation_checker.py` with:

1. **Imports:** `re`

2. **`extract_dois(references_text: str) -> list`** — **real implementation** (regex, works now):
   ```python
   def extract_dois(references_text: str) -> list:
       """Extract DOIs from the references section text using regex."""
       doi_pattern = r'\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b'
       dois = re.findall(doi_pattern, references_text, re.IGNORECASE)
       return list(set(dois))
   ```

3. **`run_citation_check(references_text: str) -> dict`** — entry point (partial implementation):
   - Extracts DOIs using `extract_dois()` (real)
   - Returns:
     ```python
     {
         "dois_found": len(extract_dois(references_text)),
         "citation_score": 5.0,   # neutral placeholder until Phase 3
         "details": "DOI extraction complete. Full citation verification (Semantic Scholar + CrossRef) coming in Phase 3."
     }
     ```
</action>

<acceptance_criteria>
- `citation_checker.py` exists in the project root
- `citation_checker.py` contains `def extract_dois(references_text: str) -> list` with working DOI regex
- `citation_checker.py` contains `def run_citation_check(references_text: str) -> dict` as the main entry point
- `extract_dois("See doi: 10.1234/test.5678 and 10.9999/another")` returns a list with 2 DOIs
- `run_citation_check("")` returns a dict with `"citation_score": 5.0`
- File can be imported without errors: `python -c "import citation_checker"`
- **No Semantic Scholar or CrossRef API calls** — those are Phase 3
</acceptance_criteria>

---

### Task 2: Report Generator Stub (report_generator.py)

<read_first>
- ResearchSense_Research.md (Section 12 — Report Generation ReportLab)
- TEAM_SUMMARY.md (Section 3 — Person 3 Responsibilities)
</read_first>

<action>
Create `report_generator.py` with:

1. **Imports:** `os`
2. **`generate_pdf_report(sections: dict, layer_scores: dict, score_result: dict, output_path: str = None) -> str`** — stub:
   - Docstring:
     ```python
     """
     Generate a structured PDF report using ReportLab.
     Full implementation in Phase 4.

     Args:
         sections: detected paper sections dict
         layer_scores: per-layer analysis results
         score_result: final score with grade
         output_path: where to save the PDF (optional, auto-generates if None)

     Returns:
         str: path to the generated PDF file
     """
     ```
   - Returns a placeholder message:
     ```python
     print("[Phase 4] PDF report generation not yet implemented")
     return ""
     ```

3. **`generate_report_data(sections: dict, layer_scores: dict, score_result: dict) -> dict`** — stub:
   - Docstring: `"""Prepare structured data for the report. Full implementation in Phase 4."""`
   - Returns:
     ```python
     {
         "status": "Report generation coming in Phase 4",
         "score_result": score_result,
         "section_count": len([v for v in sections.values() if v.strip()]) if sections else 0
     }
     ```
</action>

<acceptance_criteria>
- `report_generator.py` exists in the project root
- `report_generator.py` contains `def generate_pdf_report(sections, layer_scores, score_result, output_path=None) -> str`
- `report_generator.py` contains `def generate_report_data(sections, layer_scores, score_result) -> dict`
- File can be imported without errors: `python -c "import report_generator"`
</acceptance_criteria>

---

### Task 3: Frontend UI — Upload Page (frontend/)

<read_first>
- ResearchSense_Research.md (Section 11 — Frontend)
- TEAM_SUMMARY.md (Section 3 — Person 3 deliverable)
- .planning/phases/01-environment-pdf-parser/01-CONTEXT.md (Decision D-08 — project layout)
</read_first>

<action>
Create `frontend/` directory with three files:

**frontend/index.html:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ResearchSense — AI Paper Analysis</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>ResearchSense</h1>
            <p class="subtitle">AI-Powered Academic Paper Analysis</p>
        </header>

        <main>
            <div class="upload-section" id="uploadSection">
                <div class="drop-zone" id="dropZone">
                    <input type="file" id="fileInput" accept=".pdf" hidden>
                    <div class="drop-zone-content">
                        <span class="drop-icon">📄</span>
                        <p>Drag & drop your PDF here</p>
                        <p class="drop-hint">or <span class="browse-link" onclick="document.getElementById('fileInput').click()">browse files</span></p>
                    </div>
                </div>
                <div id="fileInfo" class="file-info" style="display: none;">
                    <span id="fileName"></span>
                    <button id="removeFile" onclick="removeFile()">✕</button>
                </div>
                <button id="analyzeBtn" onclick="analyzePaper()" disabled>Analyze Paper</button>
            </div>

            <div id="loading" class="loading-section" style="display: none;">
                <div class="spinner"></div>
                <p>Analyzing your paper... This may take 30–60 seconds.</p>
            </div>

            <div id="results" class="results-section" style="display: none;">
                <h2>Analysis Results</h2>
                <div id="scoreDisplay" class="score-display"></div>
                <div id="sectionsFound" class="sections-found"></div>
                <div id="errorDisplay" class="error-display" style="display: none;"></div>
            </div>
        </main>

        <footer>
            <p>ResearchSense &copy; 2026 — University Mini Project</p>
        </footer>
    </div>
    <script src="app.js"></script>
</body>
</html>
```

**frontend/style.css:**
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f5f7fa;
    color: #333;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.container {
    max-width: 700px;
    width: 90%;
    padding: 2rem;
}

header {
    text-align: center;
    margin-bottom: 2rem;
}

header h1 {
    font-size: 2.5rem;
    color: #1a73e8;
    margin-bottom: 0.5rem;
}

.subtitle {
    color: #666;
    font-size: 1.1rem;
}

.drop-zone {
    border: 2px dashed #ccc;
    border-radius: 12px;
    padding: 3rem 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    background: #fff;
}

.drop-zone:hover,
.drop-zone.drag-over {
    border-color: #1a73e8;
    background: #e8f0fe;
}

.drop-icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 1rem;
}

.browse-link {
    color: #1a73e8;
    cursor: pointer;
    text-decoration: underline;
}

.file-info {
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    background: #e8f0fe;
    border-radius: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.file-info button {
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: #666;
}

#analyzeBtn {
    display: block;
    width: 100%;
    margin-top: 1.5rem;
    padding: 1rem;
    font-size: 1.1rem;
    background: #1a73e8;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.3s ease;
}

#analyzeBtn:disabled {
    background: #ccc;
    cursor: not-allowed;
}

#analyzeBtn:not(:disabled):hover {
    background: #1557b0;
}

.loading-section {
    text-align: center;
    padding: 3rem;
}

.spinner {
    width: 40px;
    height: 40px;
    margin: 0 auto 1rem;
    border: 4px solid #e8f0fe;
    border-top: 4px solid #1a73e8;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.results-section {
    background: #fff;
    border-radius: 12px;
    padding: 2rem;
    margin-top: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.results-section h2 {
    margin-bottom: 1.5rem;
    color: #1a73e8;
}

.score-display {
    font-size: 1.2rem;
    margin-bottom: 1rem;
}

.sections-found {
    margin-top: 1rem;
}

.sections-found .section-item {
    padding: 0.5rem 0;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
}

.sections-found .section-item:last-child {
    border-bottom: none;
}

.section-status-found {
    color: #34a853;
    font-weight: bold;
}

.section-status-missing {
    color: #ea4335;
    font-weight: bold;
}

.error-display {
    background: #fce8e6;
    color: #c5221f;
    padding: 1.5rem;
    border-radius: 8px;
    margin-top: 1rem;
}

footer {
    text-align: center;
    margin-top: 3rem;
    color: #999;
    font-size: 0.9rem;
}
```

**frontend/app.js:**
```javascript
const API_URL = 'http://localhost:8000';

// Drag and drop handling
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');

let selectedFile = null;

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.pdf')) {
        handleFile(file);
    } else {
        alert('Please upload a PDF file.');
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    selectedFile = file;
    fileName.textContent = file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
    fileInfo.style.display = 'flex';
    analyzeBtn.disabled = false;
}

function removeFile() {
    selectedFile = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    analyzeBtn.disabled = true;
}

async function analyzePaper() {
    if (!selectedFile) {
        alert('Please select a PDF file first.');
        return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    try {
        const response = await fetch(API_URL + '/analyze', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            showError(result);
        } else {
            showResults(result);
        }
    } catch (error) {
        showError({ error: 'Connection failed', message: 'Could not connect to the server. Make sure the backend is running at ' + API_URL });
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function showResults(result) {
    const resultsDiv = document.getElementById('results');
    const scoreDisplay = document.getElementById('scoreDisplay');
    const sectionsFound = document.getElementById('sectionsFound');
    const errorDisplay = document.getElementById('errorDisplay');

    errorDisplay.style.display = 'none';

    // Show file info
    scoreDisplay.innerHTML = '<strong>File:</strong> ' + result.filename + '<br><strong>Sections detected:</strong> ' + result.section_count;

    // Show sections breakdown
    const sectionNames = ['abstract', 'introduction', 'methodology', 'results', 'discussion', 'conclusion', 'references'];
    let sectionsHTML = '<h3>Sections Breakdown</h3>';

    sectionNames.forEach(name => {
        const found = result.sections[name] && result.sections[name].trim().length > 0;
        const status = found ? '✓ Found' : '✗ Not found';
        const statusClass = found ? 'section-status-found' : 'section-status-missing';
        sectionsHTML += '<div class="section-item"><span>' + name.charAt(0).toUpperCase() + name.slice(1) + '</span><span class="' + statusClass + '">' + status + '</span></div>';
    });

    sectionsFound.innerHTML = sectionsHTML;
    resultsDiv.style.display = 'block';
    document.getElementById('uploadSection').style.display = 'block';
}

function showError(result) {
    const resultsDiv = document.getElementById('results');
    const errorDisplay = document.getElementById('errorDisplay');
    const scoreDisplay = document.getElementById('scoreDisplay');
    const sectionsFound = document.getElementById('sectionsFound');

    scoreDisplay.innerHTML = '';
    sectionsFound.innerHTML = '';

    errorDisplay.innerHTML = '<strong>' + (result.error || 'Error') + '</strong><br>' + (result.message || JSON.stringify(result));
    errorDisplay.style.display = 'block';

    resultsDiv.style.display = 'block';
    document.getElementById('uploadSection').style.display = 'block';
}
```

The frontend connects to `http://localhost:8000` — Person 1's FastAPI backend.
</action>

<acceptance_criteria>
- `frontend/index.html` exists with proper HTML5 structure, includes `style.css` and `app.js`
- `frontend/style.css` exists with styling for drop-zone, loading spinner, results display
- `frontend/app.js` exists with `analyzePaper()` function that POSTs to `http://localhost:8000/analyze`
- `frontend/app.js` handles drag-and-drop file upload
- `frontend/app.js` validates only `.pdf` files are accepted
- `frontend/app.js` shows loading indicator during analysis
- `frontend/app.js` displays section detection results (found/not found per section)
- `frontend/app.js` handles and displays error responses
- Opening `frontend/index.html` in a browser shows the upload UI
- With backend running, uploading a PDF via the UI returns and displays section results
</acceptance_criteria>

---

## Verification

### Must-Haves (derived from Phase 1 contribution)
1. ✓ `citation_checker.py` provides DOI regex extraction (real, usable now)
2. ✓ `citation_checker.py` stub entry point returns neutral citation score — Phase 3 fills in real API calls
3. ✓ `report_generator.py` defines the public API that Phase 4 will implement
4. ✓ Frontend upload page works with Person 1's backend
5. ✓ All stub files are importable without errors
6. ✓ Frontend displays section detection results from the `/analyze` endpoint

### Test Commands
```bash
# Test stub imports
python -c "import citation_checker; print(citation_checker.extract_dois('See 10.1234/test.5678'))"
python -c "import report_generator"

# Test frontend (manual)
# 1. Start backend: uvicorn main:app --reload
# 2. Open frontend/index.html in browser
# 3. Upload a PDF → should see section breakdown
```
