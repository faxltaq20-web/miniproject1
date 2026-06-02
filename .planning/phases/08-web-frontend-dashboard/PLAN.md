# Plan: Web Frontend Dashboard

**Phase:** Phase 8: Web Frontend Dashboard
**Status:** Planned
**Archetype:** Analytics Tool (Two-View SPA: Upload → Results Dashboard)

---

## Plan 1: Structural Scaffolding & Responsive Layout (HTML5)

Scaffold the semantic HTML5 structure for the single-page application. The layout consists of two toggleable view states managed client-side.

### Tasks
- [ ] Create `frontend/` directory in the project workspace.
- [ ] Create `frontend/index.html` with semantic HTML5 structuring:
  - **Header:** System logo, dashboard title, and a system diagnostics status badge (GET `/health` status).
  - **Upload View Container (`upload-view`):**
    - Drag-and-drop zone with hidden file explorer input.
    - Offline "Try Sample" action link for quota-free demo day backup.
    - 5-stage Progress Stepper checklist (Document Extraction, Section Detection, AI Analysis, Reference Verification, Report Synthesis).
  - **Results Dashboard Container (`dashboard-view`, hidden by default):**
    - **Row 1 (Hero Score Panel):** Radial SVG Score Gauge displaying target score in center + letter grade badge + recommended journal submission status pill.
    - **Row 2 (Academic Sections Grid):** Grid of detected sections indicating presence confidence (Present with % / Missing).
    - **Row 3 (2-Column Review Grid):**
      - **Left (8-column):** Restructured 5 active review layer accordion cards (Structure, Clarity, Methodology, Evidence, Citations) with collapsible issue/suggestion bullet panels.
      - **Right (4-column):** Qualitative Verdict Card and Reference Statistics summary block.
    - **Row 4 (12-column Reference List):** Scrollable table displaying each citation entry with its Semantic Scholar/CrossRef verification status badge and warnings.
    - **Row 5 (Action Footer):** Sticky download action floating button to download the ReportLab PDF.
- [ ] Include CDN links for modern Outfit/Inter fonts and Material Symbols icons in the head.

### Verification
- Opening `frontend/index.html` in a web browser renders all components structurally.
- Re-sizing the browser window validates that the 12-column Grid wrapper collapses appropriately on smaller screens.

---

## Plan 2: Professional Analytics Design System (CSS)

Build a cohesive, data-dense design system utilizing modern CSS custom properties and HSL-tailored glassmorphic styles.

### Tasks
- [ ] Create `frontend/style.css` containing:
  - **CSS Variables:** Define `--bg-base` (deep space navy), `--bg-surface` (semitransparent navy card), `--border-glow` (thin border translucency), `--text-primary`, `--text-secondary`, and semantic accent states (emerald success, amber warning, red danger, electric-blue info).
  - **Global Reset & Typography:** Lock in Outfit/Inter typography for UI text and JetBrains Mono/Fira Code for all monospace numbers, grades, metrics, and DOIs.
  - **Upload Zone Classes:** Define the dashed drop-zone pulse highlight animations.
  - **Progress Stepper Classes:** Define step checkmark icons and the pulsing glow animation for active stages.
  - **Radial SVG Circle Classes:** Set up the SVG dasharray circle animation rules (`stroke-dashoffset` transition timings).
  - **Accordion Card Classes:** Style the `.layer-card` component, including maximum height transition animations (`max-height 0.35s ease`) for collapsible issue/suggestion bullet trays.
  - **Bibliography Table Classes:** Style the scrollable reference log using JetBrains Mono fonts and semantic badging.
  - **Toast Alerts:** Style notification toast popups for file validation failures.

### Verification
- The styled static page presents a visually premium, cohesive dark dashboard with sharp typography.
- Simulating hover states on accordions and buttons reveals micro-scale transforms.

---

## 3. Plan 3: Client JavaScript Orchestration & API Connectivity (`app.js`)

Implement the JS logic to coordinate file uploads, trigger loading transitions, execute async backend fetches, and dynamically bind response data.

### Tasks
- [ ] Create `frontend/app.js` with:
  - **File Handler Bindings:** Add drag-and-drop event listeners (`dragover`, `dragleave`, `drop`) to the upload zone, validating that only `.pdf` files are parsed. Reject other files immediately using a temporary custom alert toast.
  - **Pipeline State Machine:**
    - State definitions for `upload` and `dashboard` views.
    - Implement stepper interval timings to sequentially progress stepper states (Done checkmark, active pulse, pending slate) during fetch.
  - **Analysis Fetch Trigger (`POST /analyze`):**
    - Capture file upload, pack it into a `FormData` object under field `file`, and POST to `http://localhost:8000/analyze`.
    - Handle response exceptions gracefully (e.g. 503 unavailable, 422 extraction failure) and display helpful system error messages to the user.
  - **DOM Data-Binding orchestrator:**
    - `populateDashboard(data)`: Renders all JSON values into HTML selectors.
    - `animateGauge(score)`: JS function calculating radial SVG `stroke-dashoffset` mapping `circumference * (1 - score / 100)` to animate on view toggle.
    - Detected sections grid generator mapping confidence metrics.
    - Expandable accordion details generator iterating over `layer_details` issues/suggestions.

### Verification
- Dragging a non-PDF file triggers a red validation error block.
- Uploading a valid PDF triggers the sequential stage stepper animation.
- Successful endpoint response populates all dashboard labels correctly.

---

## Plan 4: PDF Downloading & Offline Mock Demo

Wire up binary PDF streaming responses, real-time pre-flight diagnostic monitoring, and an offline backup presentation engine.

### Tasks
- [ ] **PDF Blob Downloader (`POST /report`):**
  - Bind click handler on the "Download PDF Report" action button.
  - POST the captured analysis JSON payload to `http://localhost:8000/report`.
  - Receive the `application/pdf` binary stream response, convert it to a Blob, create a temporary download URL, and trigger download dynamically.
- [ ] **Pre-Flight Diagnostics Integration (`GET /health`):**
  - Trigger call to GET `http://localhost:8000/health` on page load.
  - Update the header system status dot: green for healthy, orange/red for key expiration alerts.
- [ ] **Pre-Cached Demo Handler:**
  - Bind click handler to "Try Sample Paper".
  - Mock-progress the stepper for 1.5 seconds, load local pre-saved results from `sample_paper_data.json` values, and populate the dashboard immediately.

### Verification
- Click on "Try Sample" successfully bypasses live APIs and populates the dashboard metrics instantly.
- Clicking "Download PDF Report" fetches the ReportLab PDF in-memory and triggers a local download.
