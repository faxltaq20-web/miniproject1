# STITCH SPECIFICATION: ResearchSense Functional Web UI Requirements

This specification defines the functional frontend requirements, data display structure, API orchestration flows, and data bindings for the **ResearchSense** web application. Feed this document to **Stitch** to construct the web user interface.

---

## 1. Functional Views & Data Mappings

The frontend is a single-page application consisting of two primary views:
1. **Upload & Pipeline View:** Active during file selection, validation, and backend processing.
2. **Dashboard Results View:** Renders the parsed analytical data returned by the backend.

### 1.1 Upload & Pipeline View

#### 1.1.1 File Upload
- **Supported Interactions:**
  - Drag-and-drop of local files.
  - File selection via system file examiner.
- **Validation Constraints:**
  - Rejects any file format that is not `.pdf` instantly.
  - Displays a clear error notification message explaining the rejection.
- **Workflow Action:** Submits the file immediately to the backend analysis endpoint upon valid upload.

#### 1.1.2 Pipeline Stage Tracker
- **Activation:** Appears immediately when a valid PDF starts uploading.
- **Functionality:** Sequentially indicates the status of the following 5 backend execution steps:
  1. 📄 **Document Extraction** (*Parsing text...*)
  2. 🔍 **Academic Segmenter** (*Detecting headers & sections...*)
  3. 🧠 **Multi-Layer AI Analysis** (*Gemini deterministic scoring...*)
  4. 🔗 **Reference Verification** (*CrossRef & Semantic Scholar checks...*)
  5. 🏆 **Synthesizing Verdict** (*Compiling final grade...*)
- **Requirements:** Must clearly differentiate the currently active stage, completed stages, and pending stages.

---

### 1.2 Dashboard Results View

Displays the analysis results returned from the backend. The UI must map backend response variables to the following data displays:

#### 1.2.1 Overall Score & Grade
- **Final Numerical Score:** Displays `final_score` (representing a 0–100 scale).
- **Final Letter Grade:** Displays `grade` (e.g. `B — Good`).
- **Recommendation Status:** Maps the grade or score to one of the following four status labels:
  - `A` / `B` -> `RECOMMENDED FOR JOURNAL SUBMISSION`
  - `C` -> `MINOR REVISIONS REQUIRED`
  - `D` -> `SIGNIFICANT REVISIONS REQUIRED`
  - `F` -> `NOT READY FOR SUBMISSION`

#### 1.2.2 Detected Sections Checklist
- Displays the status of each standard academic section: Abstract, Introduction, Related Work, Methods, Results, Discussion, Conclusion, References.
- Displays whether each section is **Present** (along with the confidence score from `detected_sections`) or **Missing** (along with an explanation of why the section is missing).

#### 1.2.3 Restructured Multi-Layer Review
- Displays the score, weight, issues list, and suggestions list for each of the **5 active evaluation layers**:
  1. **Structure & Sections** (20% Weight) — Maps to key: `structure_sections`
  2. **Clarity & Writing** (25% Weight) — Maps to key: `clarity_writing`
  3. **Methodology Rigor** (25% Weight) — Maps to key: `methodology_rigor`
  4. **Evidence & Claims** (20% Weight) — Maps to key: `evidence_claims`
  5. **Citations & References** (10% Weight) — Maps to key: `citations`
- **Interactive Details:** Each layer section must support expanding/collapsing to show or hide the detailed list of **Issues** (`issues`) and **Suggestions** (`suggestions`).

#### 1.2.4 Citation & Reference Validator
- **Bibliography Statistics:** Displays numerical metrics:
  - **Total References:** Value from `total_refs`.
  - **Verified Citations:** Value from `verified`.
  - **Unverified Citations:** Total unmatched or unreachable references (`not_found` + `unreachable`).
  - **Verification Rate:** The percentage of references successfully verified.
- **Reference Entry List:**
  - Displays each bibliography reference entry.
  - Distinguishes between verified entries, duplicate references, and references flagged with missing DOIs.
  - Verified entries display their metadata (publication year, publisher, and citation count) on request or hover.

#### 1.2.5 Overall Qualitative Verdict & Actions
- **Qualitative Feedback:** Displays the text description returned by the AI verdict.
- **PDF Report Download Trigger:** Initiates a call to download the PDF version of the report.
- **API Health Diagnostics:** Displays the loaded status of systems and keys.

---

## 2. Backend API Orchestration Flow

The frontend communicates with the backend services running at `http://localhost:8000`.

### 2.1 Sanity & Key Check (`GET /health`)
- Triggers on application load.
- Executes an asynchronous GET request to `http://localhost:8000/health`.
- If the endpoint response indicates all keys are dead (e.g. `any_key_working: false`), blocks uploads and alerts the user of service unavailability.

### 2.2 Paper Analysis Request (`POST /analyze`)
- Sends a POST request to `http://localhost:8000/analyze`.
- Formats the request payload as `FormData`, appending the PDF file in a field named `file`.
- Updates the Pipeline Stage Tracker stages as the request progresses.
- On success, switches the view to the Dashboard Results View and populates all data components using the JSON response.

### 2.3 PDF Report Request (`POST /report`)
- When the user triggers the PDF download, send a POST request to `http://localhost:8000/report`.
- The request body must contain the exact, unmodified JSON payload received from the `/analyze` response.
- Handles the returned `application/pdf` binary stream, converts it into a browser Blob, and triggers the file download locally.

### 2.4 Offline Mock Demo Mode
- Displays a "Try Sample" action in the upload area.
- Clicking it bypasses active API fetch requests, displays a mock 2-second progress stepper sequence, loads local pre-cached JSON results (such as `sample_paper_data.json` values), and populates the dashboard instantly for testing.

---

## 3. Expected API JSON Data Schemas

### 3.1 `/analyze` Response JSON Structure
```json
{
  "filename": "sample_paper.pdf",
  "detected_sections": {
    "Abstract": 95,
    "Introduction": 92,
    "Methods": 88,
    "Results": 91,
    "Conclusion": 85,
    "References": 99
  },
  "section_count": 6,
  "warnings": ["discussion"],
  "layer_scores": {
    "structure_sections": 8.0,
    "clarity_writing": 7.5,
    "methodology_rigor": 6.5,
    "evidence_claims": 7.0,
    "citations": 6.0
  },
  "layer_details": {
    "structure_sections": {
      "score": 8.0,
      "issues": ["Abstract lacks a clear quantitative result statement.", "Formatting of Sub-Heading 2.1 is inconsistent."],
      "suggestions": ["Add the core numerical accuracy results to the abstract.", "Re-align Subsection 2.1 margins."]
    },
    "clarity_writing": {
      "score": 7.5,
      "issues": ["Grammar errors detected in paragraph 3 of Introduction.", "Passive voice is overused in the Methodology."],
      "suggestions": ["Convert passive sentences to active voice.", "Review spelling on Page 2."]
    },
    "methodology_rigor": {
      "score": 6.5,
      "issues": ["Dataset size is not clearly stated.", "Control group parameters are ambiguous."],
      "suggestions": ["Detail dataset sample counts.", "Formally state the control parameters."]
    },
    "evidence_claims": {
      "score": 7.0,
      "issues": ["Results fail to fully prove the accuracy claims.", "Figure 3 has missing axis labels."],
      "suggestions": ["Link empirical findings explicitly to structural claims.", "Add labels to Figure 3."]
    },
    "citations": {
      "score": 6.0,
      "issues": ["2 duplicate references detected.", "3 citations lack valid DOIs."],
      "suggestions": ["Remove duplicates.", "Provide full title search credentials."]
    }
  },
  "final_score": 71.0,
  "grade": "B — Good",
  "citation_result": {
    "total_refs": 10,
    "verified": 6,
    "not_found": 2,
    "unreachable": 2,
    "flagged_dois": ["10.1109/fake-doi"],
    "flagged_items": [
      {
        "citation": "Vaswani et al., 2017, Attention Is All You Need",
        "category": "duplicate",
        "detail": "Duplicate reference found in bibliography."
      }
    ]
  }
}
```

### 3.2 `/health` Response JSON Structure
```json
{
  "status": "healthy",
  "gemini": {
    "any_key_working": true,
    "keys_checked": 5,
    "working_keys": 4
  },
  "crossref": {
    "status": "ok"
  },
  "semantic_scholar": {
    "status": "ok"
  }
}
```
