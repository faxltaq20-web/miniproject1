## RESEARCH COMPLETE

### Phase 11 Research: Improve the Frontend UI

---

#### 1. Current Frontend State Analysis

**Files examined:** `frontend/index.html` (249 lines), `frontend/style.css` (1034 lines), `frontend/app.js` (770 lines)

##### 1.1 What Exists and Works

The Phase 8 frontend is a **fully functional single-page application** with:

- **Two-view SPA:** Upload view (`#uploadView`) and Dashboard view (`#dashboardView`)
- **Header:** Brand logo + diagnostics badge with live `/health` status dot
- **Drag-and-drop upload zone** with PDF validation, hover state, and toast rejection
- **5-stage animated stepper** (pending/active/done states with pulse animations)
- **SVG circular gauge** (stroke-dashoffset animation, score counter)
- **Grade badge + recommendation badge** with semantic color coding
- **Detected sections pill grid** (present/missing with confidence %)
- **5-layer accordion cards** (collapsible with issues/suggestions columns)
- **Verdict card** with qualitative text + Download PDF button
- **Citation metrics row** (Total/Verified/Flagged numbers)
- **Verification progress bar**
- **Reference table** with VERIFIED/DUPLICATE/INVALID DOI badges + hover tooltips
- **Slide-in toast notifications**
- **"Try Sample" demo mode** (offline pre-cached mock payload)
- **Responsive breakpoints** at 1100px and 768px

##### 1.2 Design System Already Implemented

| Token | Value |
|-------|-------|
| `--bg-base` | `#0a0e17` (deep navy) |
| `--bg-surface` | `hsla(223, 47%, 16%, 0.55)` (glass card) |
| `--bg-raised` | `hsla(223, 47%, 20%, 0.7)` |
| `--backdrop-blur` | `blur(14px)` |
| `--accent-data` | `#00E5FF` (electric cyan) |
| `--accent-success` | `#10B981` (emerald) |
| `--accent-warning` | `#F59E0B` (amber) |
| `--accent-danger` | `#EF4444` (red) |
| `--card-radius` | `16px` |
| Font UI | Inter |
| Font Header | Outfit |
| Font Data | JetBrains Mono |

##### 1.3 What Is Missing or Underdone (Identified Gaps)

**Critical Bugs:**
1. **`--space-2xl` is undefined** — used on lines 183, 278, 291 of style.css but never declared in `:root`. This causes broken padding on drop zone and stepper container.
2. **`--transition-smooth` is undefined** — used on `.layer-card` (line 605) but never declared. The layer card hover transition doesn't animate correctly.
3. **`verdict_text` field mismatch** — Backend returns `verdict_text` as a top-level field, but `app.js` reads `data.layer_details.verdict` (line 483). The verdict text never displays from live API responses.

**UI Quality Gaps:**
4. **Grade badge lacks color coding** — `grade-badge` has a static border style with no dynamic color fill/gradient based on grade. The score color is applied inline via JS but only the text color, not background gradient.
5. **No score counter animation** — The integration guide specifies a JS numeric ticker counting up from 0 to the score over 1.8s, but current `app.js` only sets the SVG offset without the counter animation.
6. **Accordion body max-height is hardcoded at 500px** — Large layers with many issues/suggestions will overflow silently (`.layer-card.open .layer-body { max-height: 500px }`). The integration guide recommends a CSS grid-rows trick for auto-height transitions.
7. **Citation table only shows flagged items + hardcoded verified samples** — Verified references display from a hardcoded array of 5 NLP papers (Vaswani, Devlin, Brown, etc.) regardless of the actual paper being analyzed. This should come from `citation_result` data.
8. **Gauge color doesn't distinguish A vs B vs C grades visually** — The stroke color sets `var(--accent-success)` for both score≥85 and score≥70 (same green). No gradient or gradient stop for intermediate scores.
9. **Section pills display % but confidence is 0-100 scale** — `pill-val` shows `${detectedVal}%` — this is correct per the API schema but visually cramped; pills only have 2 columns, all 8 sections crammed in.
10. **No layer weight labels** — The SPEC (STITCH_FRONTEND_SPEC.md §1.2.3) requires each layer to show its weight % (Structure=20%, Clarity=25%, etc.). Currently only score/10 is shown.
11. **Upload zone padding uses undefined `--space-2xl`** — visually the padding falls back to browser default (likely 0), making the drop zone look flat.
12. **No gradient body background** — `body` is flat `#0a0e17`. The guide and DESIGN.md suggest radial gradients for atmospheric depth.
13. **Mobile: hero card stacks but pills/table don't compress well below 480px** — only two breakpoints, no specific grid reduction below 480px.
14. **Stepper icons are unicode chars** (●/○/✓) — Works but plain-looking. Integration guide describes "box-shadow: 0 0 15px var(--accent-color)" pulse glow on stepper steps, currently only CSS opacity pulse on text.
15. **`recBadge` background color JS logic** — Uses a string comparison `colorClass === "var(--accent-success)"` to compute RGB values. Fragile; breaks if accent variable changes.

---

#### 2. Backend API Contract

**Confirmed from `MAIN_PROJECT/main.py`:**

##### POST /analyze — Response JSON Shape
```json
{
  "filename": "paper.pdf",
  "detected_sections": {
    "Abstract": 95,
    "Introduction": 90,
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
    "structure_sections": { "score": 8.0, "issues": [], "suggestions": [] },
    "clarity_writing":    { "score": 7.5, "issues": [], "suggestions": [] },
    "methodology_rigor":  { "score": 6.5, "issues": [], "suggestions": [] },
    "evidence_claims":    { "score": 7.0, "issues": [], "suggestions": [] },
    "citations":          { "score": 6.0, "issues": [], "suggestions": [] }
  },
  "final_score": 71.0,
  "grade": "B — Good",
  "verdict_text": "The paper presents... (AI-generated 2-3 sentence verdict)",
  "citation_result": {
    "total_refs": 10,
    "verified": 6,
    "not_found": 2,
    "unreachable": 2,
    "flagged_dois": ["10.1109/fake-doi"],
    "flagged_items": [
      { "citation": "...", "category": "duplicate", "detail": "..." }
    ]
  }
}
```

**Key note:** `verdict_text` is a **top-level field** (not nested inside `layer_details`). Current app.js reads `data.layer_details.verdict` — this is a **bug that must be fixed**.

##### POST /report — Request/Response
- Request: identical JSON body from `/analyze` response
- Response: `application/pdf` binary stream with `Content-Disposition: attachment`
- Current JS implementation is correct ✓

##### GET /health — Response Shape
```json
{
  "status": "healthy",
  "gemini": {
    "gemini_keys_loaded": 3,
    "any_key_working": true,
    "model": "gemini-2.5-flash"
  },
  "crossref": { "status": "ok" },
  "semantic_scholar": { "status": "ok" }
}
```

##### Layer Weights (from scoring.py)
| Layer Key | Label | Weight |
|-----------|-------|--------|
| `structure_sections` | Structure & Sections | 20% |
| `clarity_writing` | Clarity & Writing | 25% |
| `methodology_rigor` | Methodology Rigor | 25% |
| `evidence_claims` | Evidence & Claims | 20% |
| `citations` | Citations & References | 10% |

##### Grade Thresholds
| Score | Grade |
|-------|-------|
| ≥ 85 | A — Excellent |
| ≥ 70 | B — Good |
| ≥ 55 | C — Needs Improvement |
| ≥ 40 | D — Poor |
| < 40 | F — Very Poor |

---

#### 3. Design Spec Findings

##### From DESIGN.md (Material Design 3 token set — light theme):
> Note: DESIGN.md is a **light-theme, white-card SaaS** design system (Plus Jakarta Sans, blue primary `#001cbf`, white surfaces). This **conflicts** with the current dark glassmorphic theme. The current dark theme from Phase 8 decisions should be **maintained** — DESIGN.md appears to have been generated as a reference token set, not a replacement mandate. The Phase 8 decisions (D-02) explicitly chose dark glassmorphic.

**DESIGN.md relevant quality chips spec:**
- Status chips use low-opacity background tint + high-contrast text of same hue
- Cards: 12px radius, 24px internal padding, soft ambient shadow
- Tables: horizontal dividers only, ample cell padding, active row blue tint

##### From STITCH_FRONTEND_SPEC.md (canonical frontend spec):
Key requirements that are **not yet implemented**:
- §1.2.1: Recommendation maps grade `A/B → "RECOMMENDED FOR JOURNAL SUBMISSION"`, `C → "MINOR REVISIONS REQUIRED"`, `D → "SIGNIFICANT REVISIONS REQUIRED"`, `F → "NOT READY FOR SUBMISSION"` — current implementation uses score thresholds (≥85, ≥70, ≥55, ≥40) which doesn't exactly match grade-based mapping
- §1.2.3: Each layer must show **score + weight + issues + suggestions**. Weight labels (20%, 25%, etc.) are **missing** from current accordion headers
- §1.2.4: Reference entry list must distinguish verified entries, duplicates, and missing-DOI entries. Flagged/duplicates **must appear at top**. Verified entries show metadata on hover. Current table shows flagged first but uses hardcoded titles for verified rows.

##### From FRONTEND_INTEGRATION_GUIDE.md:
Key UI enhancement specs:
- **Score counter ticker** (§4.3): JS animation counting from 0 to score over 1.8s
- **Accordion smooth expand** (§4.4): CSS grid-rows 0fr→1fr transition preferred over max-height
- **Flagged citations at top** (§4.5): "Flagged or duplicate DOIs must be positioned at the **top** of the bibliography"
- **Stepper glow pulse** (§4.2): Active stages use `box-shadow: 0 0 15px var(--accent-color)` breathing glow
- **Failover handling** (§5.1): When `final_score === 0.0`, show friendly "Gemini rate-limited" message + offer Demo mode

##### From desirable.md:
- Grade recommendation rule: A→"ready for submission", B→"minor revision", C→"major revision", D/F→"not suitable"
- This is grade-based, not score-threshold-based → aligns with STITCH_SPEC recommendation mapping

---

#### 4. UI Improvement Opportunities

Listed from highest to lowest impact:

##### P0 — Bugs (Must Fix)
| # | Gap | File | Impact |
|---|-----|------|--------|
| B1 | `--space-2xl` undefined — drop zone and stepper container padding broken | style.css | Drop zone looks flat, padding is 0 |
| B2 | `--transition-smooth` undefined — layer card hover has no animation | style.css | Accordion cards feel static |
| B3 | `verdict_text` field mismatch — verdict never shows on live API | app.js L483 | Verdict card always blank on live API |

##### P1 — High Value UX Improvements
| # | Gap | File | Improvement |
|---|-----|------|-------------|
| U1 | No score counter ticker animation | app.js | Add numeric counter from 0→score over 1.8s |
| U2 | Layer weight labels missing | app.js | Add "20%" weight badge to each layer header |
| U3 | Grade recommendation mapping inconsistent | app.js | Switch to grade-letter-based mapping (A/B → recommended, C → minor revisions, D/F → not ready) |
| U4 | Citation table verified rows are hardcoded | app.js | Show actual `citation_result` data; remove hardcoded NLP paper titles |
| U5 | Grade badge has no background color — just text color | app.js + style.css | Add gradient background fill to grade-badge per grade |
| U6 | Gauge color flat (same green for A and B) | app.js | Add score-range gradient: emerald≥85, blue-green 70-84, amber 55-69, red<55 |

##### P2 — Premium Polish
| # | Gap | File | Improvement |
|---|-----|------|-------------|
| P1 | Accordion expand uses max-height:500px | style.css | Switch to CSS grid-rows: 0fr→1fr for auto-height |
| P2 | Stepper active state uses only text pulse, no glow box-shadow | style.css | Add `box-shadow: 0 0 12px var(--accent-data)` to active step icon |
| P3 | Body background is flat navy | style.css | Add subtle radial gradient (dark navy center → deeper edges) |
| P4 | Flagged citations should appear at top of reference table | app.js | Reorder: flagged_items + flagged_dois first, then verified |
| P5 | `final_score === 0.0` has no failover UI | app.js | Add friendly Gemini rate-limit message + demo offer |
| P6 | Drop zone icon is emoji 📄 | index.html | Upgrade to inline SVG for crisp rendering |
| P7 | Hero card left border is just 1px rule | style.css | Improve visual separator between gauge and sections grid |
| P8 | No visual feedback on section pills for "Missing" reason | index.html + app.js | Add tooltip explaining why section is missing (from `warnings` array) |
| P9 | `citeUnverified` computation: `not_found + unreachable` correct but no "unreachable" badge type | app.js | Add third badge type "UNREACHABLE" (amber) vs "NOT FOUND" (red) for flagged_dois |
| P10 | Demo button text is plain link style | style.css | Upgrade to outlined button with icon for better discoverability |

---

#### 5. Implementation Approach

##### 5.1 CSS Fixes (style.css)

Add to `:root`:
- `--space-2xl: 48px;` — Fix B1
- `--transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);` — Fix B2

Accordion grid-rows trick:
```css
.layer-body {
    display: grid;
    grid-template-rows: 0fr;
    transition: grid-template-rows 0.35s ease;
    overflow: hidden;
    padding: 0 20px;
}
.layer-body-inner { min-height: 0; }
.layer-card.open .layer-body { grid-template-rows: 1fr; }
```

Stepper active glow:
```css
.step.active .step-icon {
    color: var(--accent-data);
    box-shadow: 0 0 12px var(--accent-data);
    border-radius: 50%;
}
```

Body radial gradient:
```css
body {
    background: radial-gradient(ellipse at 30% 20%, hsla(223, 60%, 18%, 0.8) 0%, var(--bg-base) 65%);
}
```

Grade badge color classes (applied via JS):
```css
.grade-badge.grade-a { background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(16,185,129,0.05)); border-color: rgba(16,185,129,0.4); color: #10B981; }
.grade-badge.grade-b { background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(59,130,246,0.05)); border-color: rgba(59,130,246,0.4); color: #60a5fa; }
.grade-badge.grade-c { background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.05)); border-color: rgba(245,158,11,0.4); color: #F59E0B; }
.grade-badge.grade-d, .grade-badge.grade-f { background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.05)); border-color: rgba(239,68,68,0.4); color: #EF4444; }
```

Layer weight chip:
```css
.layer-weight {
    font-family: var(--font-data);
    font-size: 11px;
    color: #64748b;
    background: var(--bg-raised);
    padding: 2px 8px;
    border-radius: 99px;
    border: 1px solid var(--border-subtle);
}
```

##### 5.2 JavaScript Fixes (app.js)

**Fix B3 — verdict_text field:**
Change from `data.layer_details.verdict` to `data.verdict_text || data.layer_details?.verdict || "No feedback generated."`

**Fix U1 — Score counter ticker:**
```javascript
function animateScore(targetScore) {
    let count = 0;
    const duration = 1800;
    const increment = duration / targetScore;
    const timer = setInterval(() => {
        count++;
        document.getElementById("gaugeScoreText").textContent = count;
        if (count >= targetScore) clearInterval(timer);
    }, increment);
}
```

**Fix U2 — Layer weight labels:**
```javascript
const activeLayers = [
    { key: "structure_sections", label: "Structure & Sections", num: "01", weight: "20%" },
    { key: "clarity_writing",    label: "Clarity & Writing",    num: "02", weight: "25%" },
    { key: "methodology_rigor",  label: "Methodology Rigor",    num: "03", weight: "25%" },
    { key: "evidence_claims",    label: "Evidence & Claims",    num: "04", weight: "20%" },
    { key: "citations",          label: "Citations & References", num: "05", weight: "10%" }
];
```

**Fix U3 — Grade-based recommendation mapping:**
```javascript
function getRecommendationFromGrade(grade) {
    if (grade.startsWith("A") || grade.startsWith("B")) return { text: "RECOMMENDED FOR JOURNAL SUBMISSION", color: "var(--accent-success)" };
    if (grade.startsWith("C")) return { text: "MINOR REVISIONS REQUIRED", color: "var(--accent-warning)" };
    if (grade.startsWith("D")) return { text: "SIGNIFICANT REVISIONS REQUIRED", color: "var(--accent-danger)" };
    return { text: "NOT READY FOR SUBMISSION", color: "var(--accent-danger)" };
}
```

**Fix U4 — Citation table with real data:**
- Show flagged_items (DUPLICATE badge) — real data
- Show flagged_dois (INVALID DOI badge) — real data
- For verified entries: show summary row "X citations verified via Semantic Scholar" (count from `citation_result.verified`)

**Fix P5 — Failover UI for score=0:**
```javascript
if (data.final_score === 0.0) {
    showToastNotification("⚠ Gemini analysis returned 0 — API quota may be exhausted. Try the sample demo.", false);
}
```

##### 5.3 HTML Changes (index.html)
- Add `class="layer-body-inner"` wrapper div inside `.layer-body` for grid-rows trick
- Optionally: swap emoji drop icon 📄 for inline SVG

---

#### 6. Files to Create/Modify

| File | Action | Scope |
|------|--------|-------|
| `frontend/style.css` | Modify | Add `--space-2xl`, `--transition-smooth` to `:root`; update `.layer-body` to CSS grid-rows trick; add stepper glow; add grade badge color classes; add `.layer-weight` chip style; add body radial gradient; add `.ref-badge.unreachable` style |
| `frontend/app.js` | Modify | Fix verdict_text field; add score counter ticker; add layer weight labels; fix grade recommendation mapping; replace hardcoded verified titles with real data pattern; add failover 0-score UI; fix grade badge class assignment |
| `frontend/index.html` | Modify (minor) | Add `div.layer-body-inner` wrapper for CSS grid-rows; optionally upgrade emoji icon to SVG |

**No backend changes required.** The FastAPI backend is complete and correct.

---

#### 7. Risks & Dependencies

| Risk | Severity | Mitigation |
|------|----------|------------|
| **DESIGN.md is a light-theme spec** — conflicts with current dark glassmorphic theme | Low | Confirmed via Phase 8 decisions (D-02): dark glassmorphic is canonical. Ignore DESIGN.md color tokens. |
| **CSS grid-rows accordion trick requires inner wrapper div** — HTML change needed | Low | Must add `div.layer-body-inner` inside accordion body in both index.html AND the JS that dynamically generates accordion cards |
| **Verified citation titles are not returned by API** — backend only returns `verified` count, not individual paper titles | Medium | Use count summary row ("X citations verified via Semantic Scholar") instead of fake titles |
| **Accordion max-height change may affect existing open state** — CSS grid-rows requires restructuring the `.layer-card.open` rule | Low | Test demo mode after change |
| **Demo mode mock payload has `layer_details.verdict`** (not `verdict_text`) | Medium | Fix must use `data.verdict_text \|\| data.layer_details?.verdict` for backward compat with demo payload |
| **`--space-2xl` was undefined all along in Phase 8** — fixing it will visually change the drop zone size | Low | Visual improvement, not a regression |

#### Key Decisions for the Planner

1. **Verified citation rows:** Show a single "X verified citations — Semantic Scholar" summary row (no fake titles)
2. **Fonts:** Keep Outfit/Inter — do NOT adopt DESIGN.md's Plus Jakarta Sans
3. **Mobile 480px breakpoint:** Add a third breakpoint at 480px for pill grid and table
4. **Drop icon:** Upgrade emoji 📄 to inline SVG for crisp HiDPI rendering

---
*Research gathered: 2026-06-11*
*Source files: STATE.md, REQUIREMENTS.md, ROADMAP.md, PROJECT.md, frontend/index.html, frontend/style.css, frontend/app.js, DESIGN.md, STITCH_FRONTEND_SPEC.md, FRONTEND_INTEGRATION_GUIDE.md, desirable.md, MAIN_PROJECT/main.py, MAIN_PROJECT/scoring.py, phases/08-web-frontend-dashboard/*
