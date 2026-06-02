# Phase 8: Web Frontend Dashboard - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the client-facing Web Frontend Dashboard for the ResearchSense application. This dashboard connects to the FastAPI backend, provides a highly responsive, modern, glassmorphic UI, visualizes multi-layer academic reviews and section detection results, and coordinates interactive PDF report downloading.

**What this phase includes:**
- **Visual Design System:** Glassmorphic modern dark mode with Outfit/Inter typography, deep space backgrounds, HSL semitransparent cards, and micro-animations.
- **File Upload & Stage Stepper:** Drag-and-drop PDF-only zone with a dynamic 5-stage progress indicator representing real-time backend pipeline completion.
- **Score & Verdict Dashboard:** Animating radial SVG progress gauge, color-coded Grade Pill, clinical recommendation status, and premium Verdict Card.
- **Multi-Layer Review Breakdown:** Interactive expandable cards for the restructured 5 evaluation layers showing raw scores, weights, specific issues, and actionable suggestions.
- **Citation Quality & DOI Checker Panel:** Total references, verification success rates, and an interactive reference list with CrossRef/Semantic Scholar status badges and hover tooltips.
- **PDF Streaming Action:** Integrating with the backend `/report` endpoint to stream in-memory ReportLab PDFs directly to the user's browser.
- **Try Samples Demo Mode:** Offline pre-cached mock JSON loader to safely demo the dashboard without hitting free-tier API quotas.
- **API Diagnostics Indicator:** Pre-flight client checks calling the FastAPI GET `/health` endpoint to display system readiness.

**What this phase does NOT include:**
- User accounts, databases, or cloud storage (stateless file handling remains strict).
- Plagiarism checking.
- Mobile application wrappers (standard responsive desktop web layout is target).

</domain>

<decisions>
## Implementation Decisions

### 1. Visual Identity & Architecture
- **D-01 (Modern Vanilla Stack):** Build the frontend using pure Semantic HTML5, Vanilla CSS3 (CSS variables, backdrop-filter, flexbox, CSS Grid), and modern Vanilla JavaScript (ES6+, async/await fetch, FormData). Bypasses heavy frameworks (React/Vue/Next.js) to guarantee 0ms compile time and rapid client-side rendering.
- **D-02 (Glassmorphism & Contrast):** Set a deep space navy background (`hsl(222, 47%, 11%)`) with subtle radial gradients, using glassmorphic surfaces (`backdrop-filter: blur(12px)`) and thin glowing borders for cards. Use **Inter** or **Outfit** typography.

### 2. Upload Flow & Stage Stepper
- **D-03 (Strict PDF Filter):** Accept `.pdf` only. Instantly reject other file types on drop or select with a customized animated toast notification.
- **D-04 (5-Stage Stepper):** Create a dynamic stage stepper that updates sequentially to represent backend progress:
  1. 📄 *Extracting Document Text...*
  2. 🔍 *Detecting Academic Sections...*
  3. 🧠 *Running Multi-Layer AI Analysis...*
  4. 🔗 *Verifying Citations & References...*
  5. 🏆 *Compiling Report Lab PDF...*

### 3. Analytics Dashboard & Interactive Panels
- **D-05 (Circular SVG Gauge):** Build an animated SVG dasharray circle that counts up from `0` to the final paper score. Theme the grade pill emerald green (`A`), gold/amber (`B`), orange (`C`), and rose red (`D`/`F`).
- **D-06 (Detected Sections Pill Grid):** Render an 8-pill layout indicating detected academic sections. Detected sections glow green; missing sections are muted gray with tooltips explaining the omission.
- **D-07 (Expandable Review Cards):** Build interactive accordion cards for the 5 active restructured evaluation layers. Clicking a card slides open a detailed view containing list items for specific issues (red warning icons) and suggestions (green success icons).
- **D-08 (Citation Metadata Panel):** Display total citations, verified count, and success rate. List all references in a scrollable container with status badges. Hovering over verified badges dynamically reveals citation counts and publication years in tooltips.

### 4. PDF Integration & Pre-Flight Diagnostics
- **D-09 (Streamed In-Memory PDF):** Connect the "Download PDF" button to a fetch request that POSTs the stored `/analyze` JSON response to the `/report` endpoint, triggers browser download of the returned binary blob, and avoids storing files on the server.
- **D-10 (Pre-Cached Demo Mode):** Provide "Try Sample" buttons. Clicking a sample instantly loads a local, pre-saved JSON payload (e.g. from `sample_paper_data.json`) and populates the dashboard, enabling offline demonstrations without consuming API keys.
- **D-11 (Pre-Flight Diagnostics Indicator):** Display a small system status badge that polls `GET /health` on load and alerts the user if Gemini or citation lookup services are unresponsive.

</decisions>

<canonical_refs>
## Canonical References

### Project Scope
- `.planning/FRONTEND_REQUIREMENTS.md` — Complete frontend visual and component specification
- `.planning/PROJECT.md` — Core value, primary user context, tech stack decisions
- `.planning/REQUIREMENTS.md` — Mapped requirements (`REP-03`, `REP-04`)
- `.planning/ROADMAP.md` — Phase 8 roadmap entry

### Backend Endpoints to Consume
- `GET /` — Root API sanity check
- `GET /health` — Diagnostic health check
- `POST /analyze` — Upload PDF to receive structured JSON
- `POST /report` — Post JSON analysis data to receive binary streaming PDF

</canonical_refs>

<code_context>
## Existing Code Insights

### Backend orchestrator `main.py` endpoints:
```python
# CORS middleware is already enabled on backend:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### PDF Streaming Response syntax:
```python
# POST /report expects:
# JSON body matching the analyze output
# Returns: application/pdf as StreamingResponse
```

### Pre-cached Mock JSON structure:
- Local sample analysis results are available in `MAIN_PROJECT/sample_paper_data.json`.

</code_context>

<deferred>
## Deferred Ideas
- **User Authentication / Paper History Caching:** Deferred to maintain absolute stateless privacy.
- **Interactive PDF Annotator:** Deferred.

</deferred>

***

*Phase: 08-web-frontend-dashboard*
*Context gathered: 2026-06-02*
