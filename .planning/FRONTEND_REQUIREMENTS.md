# FRONTEND REQUIREMENTS: ResearchSense Web Dashboard

**Date:** June 02, 2026
**Target Audience:** University Professors (Primary), Students (Secondary)
**Design Philosophy:** Premium Academic Clinical, Sleek Glassmorphic, Highly Interactive

---

## 1. Design Aesthetics & Visual Identity

To wow the grading professor at first glance, the frontend must move completely away from standard bootstrap/generic templates. It must feel premium, modern, and state-of-the-art.

### 1.1 Color Palette (Harmonious Sleek Dark Mode)
We will implement a premium dark/light adaptive design or a default rich dark mode with HSL-tailored colors:
- **Primary (Core Brand):** Deep Indigo to Indigo-Violet Gradient (`hsl(238, 83%, 60%)` to `hsl(262, 83%, 58%)`)
- **Background:** Deep space navy (`hsl(222, 47%, 11%)`) with subtle radial gradients for depth
- **Surface (Glassmorphic Cards):** Semitransparent navy (`hsla(223, 47%, 16%, 0.6)`) with a fine, translucent border (`hsla(0, 0%, 100%, 0.08)`) and backdrop-filter blur (`12px`)
- **Muted Text:** Pale Slate (`hsl(215, 20%, 65%)`)
- **Core Semantic Colors:**
  - **Success / Validated:** Emerald Green (`hsl(142, 70%, 45%)`)
  - **Warning / Issue:** Orange / Amber (`hsl(35, 92%, 50%)`)
  - **Danger / Error / Flagged:** Rose Red (`hsl(346, 84%, 61%)`)
  - **Information / Neutral:** Electric Blue (`hsl(199, 89%, 48%)`)

### 1.2 Typography
- Standard sans-serif defaults will be bypassed in favor of a modern, clean typeface from Google Fonts.
- **Brand & Headings:** **Outfit** or **Inter** (clean, wide, modern geometry)
- **Monospace Elements (DOIs/Stats):** **JetBrains Mono** or **Fira Code** (high readability for technical metadata)

### 1.3 Micro-Animations & Dynamic States
- **Smooth Transitions:** Hover states must have micro-transitions (`all 0.3s cubic-bezier(0.4, 0, 0.2, 1)`)
- **Drag & Drop Pulsing:** The upload zone must pulse gently on hover or drag-over
- **Result Score Gauge:** The circle score gauge must animate from 0 to the target score on page load
- **Shimmer Loading State:** Skeletons with a moving gradient highlight to indicate active processing

---

## 2. Page & Component Specification

### 2.1 File Upload & Pipeline Stage Tracker (Main View)
This view handles the initial file upload.
- **Glassmorphic Drop-Zone:**
  - Drag-and-drop capability for PDF files
  - Fallback file explorer search
  - Strict validator: rejects any file format other than `.pdf` instantly with a red toast notification
- **Interactive Multi-Stage Loader:**
  - Standard spinner is replaced with a **Horizontal/Vertical Stepper** showing real-time backend pipeline stages:
    1. 📄 **Extracting Document Text** (PyMuPDF with PyMuPDF4LLM fallback)
    2. 🔍 **Detecting Academic Sections** (Identifying Abstract, Intro, Methods, etc.)
    3. 🧠 **Multi-Layer AI Analysis** (Running Gemini 2.5 Flash deterministic evaluation)
    4. 🔗 **Validating Citations** (Checking DOIs via CrossRef & Titles via Semantic Scholar)
    5. 🏆 **Synthesizing Verdict & Report** (Calculating scoring matrix & generating PDF)
  - Shows active pulse animation next to the current stage, green checkmarks next to completed stages, and an estimate of the remaining time (~10–25s total).

### 2.2 Main Dashboard (Results View)
Once the `/analyze` endpoint completes, the interface transitions seamlessly into the analytics dashboard.

#### 2.2.1 Hero Score Panel
- **Score Dial:** A premium circular svg progress gauge displaying the final score (e.g. `74.0/100`) in the center
- **Grade Pill:** A prominent, glowing badge (e.g. `B — Good`, `D — Poor`) with matching colored text and border
- **Recommendation Status:** A badge showing clinical actionability:
  - `A` / `B` -> `✅ RECOMMENDED FOR JOURNAL SUBMISSION`
  - `C` -> `⚠️ MINOR REVISIONS REQUIRED`
  - `D` -> `❌ SIGNIFICANT REVISIONS REQUIRED`
  - `F` -> `🚫 NOT READY FOR SUBMISSION`

#### 2.2.2 Detected Sections Pill-Grid
- Displays the parsed sections: Abstract, Introduction, Related Work, Methods, Results, Discussion, Conclusion, References
- Color-coded:
  - **Green Pill:** Section detected with high confidence
  - **Muted Gray Pill:** Section missing or not detected (displays warning tooltips)

#### 2.2.3 Interactive Multi-Layer Analysis Grid
- Displays the 5 evaluation layers matching our restructured backend scoring weights:
  1. **Structure & Sections** (20%)
  2. **Clarity & Writing** (25%)
  3. **Methodology Rigor** (25%)
  4. **Evidence & Claims** (20%)
  5. **Citations & References** (10%)
- **Card Design:** Each layer is represented as a glassmorphic card with a colored top-border corresponding to its score (Green for >=8.5, Gold for >=7.0, Orange for >=5.5, Red below).
- **Collapsible / Expandable Details:**
  - Click to expand issues list and recommendations list
  - **Issues (Red icon):** Specific bullet points detailing what is wrong
  - **Suggestions (Green icon):** Actionable items detailing how to fix it

#### 2.2.4 Advanced Citation Quality & Reference Validator
- **Citation Stats Row:**
  - **Total References Count:** Total references extracted
  - **Verified Citations:** References successfully matched on CrossRef/Semantic Scholar
  - **Unverified Citations:** References unmatched or missing DOI/Title verification
  - **Verification Rate:** Success percentage bar
- **Filterable References List:**
  - List of references with active badges: `[VERIFIED via CrossRef]`, `[VERIFIED via Semantic Scholar]`, `[FLAGGED: Missing DOI]`, `[FLAGGED: Duplicate]`
  - Hovering over verified items reveals metadata (Year, Publisher, Citation Count) in a sleek tooltip.

#### 2.2.5 Overall Clinical Verdict Card
- A wide, premium glowing card featuring the AI-synthesized qualitative feedback paragraph.
- Includes a copy-to-clipboard button and a quick summary pill list.

---

## 3. Key Actions & Integrations

### 3.1 PDF Report Download Action
- A prominent floating or static action button: **"Download Analysis PDF"**
- **Orchestration Flow:**
  - The frontend captures the JSON results returned from the `/analyze` endpoint.
  - Clicking the button sends a `POST` request containing this JSON to the `/report` endpoint.
  - The backend generates the ReportLab PDF in-memory, returns it as a streaming binary file, and the browser triggers an immediate download (e.g. `Attention_Is_All_You_Need_report.pdf`).
  - No server-side storage required, preserving privacy.

### 3.2 Live Pre-Flight Health Diagnostics
- A small **System Health indicator** in the footer or settings panel.
- Periodically calls `GET /health` to display live API connectivity status:
  - Gemini API: `Connected (Active / 0.0s latency)`
  - Semantic Scholar API: `Connected`
  - CrossRef API: `Connected`
  - Prevents users from uploading papers when API keys are exhausted or quotas are hit, showing a useful system warning instead.

### 3.3 Offline Pre-Cached Demo Mode
- To protect free API quotas during live evaluation/demo day, the UI will feature a **"Demo / Try Samples"** section.
- Selecting a sample paper (e.g., "Transformer Paper (B - Good)") bypasses the live API call and immediately loads a pre-saved local JSON analysis response, demonstrating all UI components instantly with 0 latency.

---

## 4. Technical Stack

To maintain clean, lightweight, highly performant architecture without adding heavy framework compilation overhead:
1. **Core Structure:** Semantic HTML5
2. **Styling & Presentation:** Modern Vanilla CSS (using CSS Custom Properties for themes, backdrop-filter blur, CSS grids, and flexbox)
3. **Application Logic:** Vanilla Modern JavaScript (ES6+, using async/await fetch, FormData, and dynamic DOM manipulation)
4. **Icons:** SVG-based inline icons (or Feather Icons) for sharp rendering on high-DPI displays.
