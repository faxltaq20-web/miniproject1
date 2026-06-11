---
phase: 11
title: "Improve the Frontend UI"
wave: 1-5
depends_on: []
files_modified:
  - frontend/style.css
  - frontend/app.js
  - frontend/index.html
autonomous: true
---

# Phase 11 Plan: Improve the Frontend UI

## Overview

This plan improves the ResearchSense frontend across three files — `frontend/style.css`, `frontend/app.js`, and `frontend/index.html` — using an **additive-only** approach. No existing elements, IDs, classes, or event listeners are removed. Work is organized into 5 waves so that CSS bug fixes land first (all other waves depend on them), then HTML structural prep, then accordion CSS, then parallel JS fixes and enhancements.

**Constraint:** All changes are purely additive or targeted replacements of broken/incorrect logic. Every existing HTML element, CSS selector, and JS function is preserved.

---

## must_haves

- [ ] `--space-2xl: 48px` and `--transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1)` added to `:root` in `style.css`
- [ ] Body has radial gradient background
- [ ] Grade badge shows color-coded gradient by grade letter (A/B/C/D/F classes)
- [ ] Score gauge uses score-range colors (emerald/cyan/amber/red)
- [ ] Score counter ticker animates from 0 to final_score on dashboard render
- [ ] Layer accordion headers show weight labels (`20%`, `25%`, etc.)
- [ ] Citation table uses real API data (no hardcoded NLP paper titles)
- [ ] Grade recommendation uses grade-letter-based text (not score thresholds)
- [ ] `verdict_text` field read from top-level `data.verdict_text` with fallback
- [ ] 480px mobile breakpoint added

---

## Artifacts This Phase Produces

- **`frontend/style.css`** — new CSS vars (`--space-2xl`, `--transition-smooth`), body radial gradient, grade badge color classes, `.layer-weight` chip, accordion grid-rows trick, stepper active glow, `.ref-badge.unreachable`, 480px breakpoint
- **`frontend/app.js`** — score ticker animation, grade badge class assignment, gauge stroke color by score range, weight labels in layer accordion headers, grade-letter-based rec badge logic, `verdict_text` fix, citation table data fix (remove hardcoded titles), score=0 failover toast, `.layer-body-inner` wrapper in JS template
- **`frontend/index.html`** — SVG drop icon (replaces emoji 📄), `.layer-body-inner` wrapper div inside static accordion `.layer-body`

---

## Wave 1 — CSS Bug Fixes (must execute first; all other waves depend on these)

These fix undefined CSS variables and missing utility classes that are already referenced by the existing code.

---

### Task 1.1 — Add missing CSS variables `--space-2xl` and `--transition-smooth` to `:root`

**read_first:**
- `frontend/style.css` (lines 6–41, the `:root` block)

**action:**
Inside the `:root` block in `style.css`, after the existing `--space-xl: 32px;` line (currently line 40), add two new lines:
```css
    --space-2xl: 48px;
    --transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
```
These variables are already used by `.drop-zone` (line 183), `.demo-trigger-container` (line 278), `.stepper-container` (line 291), and `.layer-card` (line 605) but were never declared, causing the padding to fall back to `0` and the hover transition to be inoperative.

**acceptance_criteria:**
- `:root` in `style.css` contains `--space-2xl: 48px;`
- `:root` in `style.css` contains `--transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);`
- No other lines in `:root` are changed or removed

---

### Task 1.2 — Add body radial gradient to `body` rule in `style.css`

**read_first:**
- `frontend/style.css` (lines 51–56, the `body` block)

**action:**
In the existing `body` rule (currently lines 51–56), add the radial gradient background property alongside the existing `background-color`. The full updated `body` rule should be:
```css
body {
    background-color: var(--bg-base);
    background: radial-gradient(
        ellipse at 30% 20%,
        hsla(223, 60%, 18%, 0.8) 0%,
        var(--bg-base) 65%
    );
    min-height: 100vh;
    color: #f1f5f9;
    overflow-x: hidden;
    line-height: 1.5;
}
```
Keep `background-color` as a fallback above the `background` shorthand. Add `min-height: 100vh`.

**acceptance_criteria:**
- `body` rule in `style.css` contains a `background:` property with `radial-gradient(ellipse at 30% 20%, ...)`
- `body` rule still contains `background-color: var(--bg-base);` as a fallback
- `body` rule contains `min-height: 100vh;`
- All other `body` properties (`color`, `overflow-x`, `line-height`) are preserved

---

### Task 1.3 — Add grade badge color classes to `style.css`

**read_first:**
- `frontend/style.css` (lines 514–534, the `.grade-badge` and `.rec-badge` blocks)

**action:**
After the existing `.rec-badge` block (ending around line 534), append these new CSS rules. Do NOT modify the existing `.grade-badge` base class:
```css
/* Grade Badge — color-coded by grade letter (class added via JS) */
.grade-badge.grade-a {
    background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(16,185,129,0.05));
    border-color: rgba(16,185,129,0.4);
    color: #10B981;
}

.grade-badge.grade-b {
    background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(59,130,246,0.05));
    border-color: rgba(59,130,246,0.4);
    color: #60a5fa;
}

.grade-badge.grade-c {
    background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(245,158,11,0.05));
    border-color: rgba(245,158,11,0.4);
    color: #F59E0B;
}

.grade-badge.grade-d {
    background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05));
    border-color: rgba(239,68,68,0.4);
    color: #EF4444;
}

.grade-badge.grade-f {
    background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05));
    border-color: rgba(239,68,68,0.4);
    color: #EF4444;
}
```

**acceptance_criteria:**
- `style.css` contains `.grade-badge.grade-a`, `.grade-badge.grade-b`, `.grade-badge.grade-c`, `.grade-badge.grade-d`, `.grade-badge.grade-f` rules
- Each rule has a `background: linear-gradient(...)`, `border-color`, and `color` property
- Existing `.grade-badge` base class is untouched

---

### Task 1.4 — Add `.layer-weight` chip CSS to `style.css`

**read_first:**
- `frontend/style.css` (lines 645–665, the `.layer-meta-block` and `.layer-score` blocks)

**action:**
After the existing `.layer-chevron` block (ending around line 665), append this new rule:
```css
/* Layer Weight Chip — shown in accordion header meta block */
.layer-weight {
    font-family: var(--font-data);
    font-size: 11px;
    letter-spacing: 0.03em;
    color: #64748b;
    background: var(--bg-raised);
    padding: 2px 8px;
    border-radius: 99px;
    border: 1px solid var(--border-subtle);
}
```

**acceptance_criteria:**
- `style.css` contains a `.layer-weight` rule
- `.layer-weight` has `font-family: var(--font-data)`, `font-size: 11px`, `border-radius: 99px`, and `border: 1px solid var(--border-subtle)`

---

### Task 1.5 — Add `.ref-badge.unreachable` CSS to `style.css`

**read_first:**
- `frontend/style.css` (lines 898–922, the `.ref-badge` block and existing badge variants)

**action:**
After the existing `.ref-badge.warning` block (ending around line 922), append this new variant:
```css
.ref-badge.unreachable {
    background: rgba(245,158,11,0.15);
    color: #F59E0B;
    border: 1px solid rgba(245,158,11,0.3);
}
```
This is an amber variant distinct from `.ref-badge.danger` (red) and `.ref-badge.warning` (existing orange-red). It represents citations that timed out/were unreachable rather than invalid.

**acceptance_criteria:**
- `style.css` contains `.ref-badge.unreachable` with amber `color: #F59E0B` and matching `background` and `border`
- Existing `.ref-badge.success`, `.ref-badge.danger`, `.ref-badge.warning` rules are untouched

---

### Task 1.6 — Add stepper active glow rule to `style.css`

**read_first:**
- `frontend/style.css` (lines 363–388, the stepper active/done state block)

**action:**
The existing `.step.active .step-icon` rule (lines 364–367) only sets `color` and `animation`. Extend it by adding `box-shadow` and `border-radius` properties. The updated rule should be:
```css
.step.active .step-icon {
    color: var(--accent-data);
    animation: active-pulse 1.2s ease-in-out infinite;
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.5);
    border-radius: 50%;
    padding: 2px;
}
```
This is a targeted modification of the existing rule — the `color` and `animation` lines are preserved; `box-shadow`, `border-radius`, and `padding` are added.

**acceptance_criteria:**
- `.step.active .step-icon` in `style.css` contains `box-shadow: 0 0 12px rgba(0, 229, 255, 0.5);`
- `.step.active .step-icon` still contains `color: var(--accent-data);` and `animation: active-pulse 1.2s ease-in-out infinite;`

---

### Task 1.7 — Add 480px mobile breakpoint to `style.css`

**read_first:**
- `frontend/style.css` (lines 991–1034, the existing `@media` blocks)

**action:**
After the closing brace of the existing `@media (max-width: 768px)` block (ending at line 1033), append a new breakpoint block:
```css
@media (max-width: 480px) {
    .sections-grid {
        grid-template-columns: 1fr;
    }

    .ref-table-wrap {
        overflow-x: scroll;
    }

    .cite-metrics {
        flex-direction: column;
        gap: 8px;
    }

    .grade-row {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }
}
```
Note: `sections-grid` is the pill grid class used at this viewport. The existing `.section-pill-grid` already gets `grid-template-columns: 1fr` at 768px; this targets `sections-grid` used at narrower viewports. `.ref-table-wrap`, `.cite-metrics`, `.grade-row` are semantic class names used in the dashboard.

**acceptance_criteria:**
- `style.css` contains an `@media (max-width: 480px)` block
- The block contains at least `flex-direction: column` for `.cite-metrics` and `.grade-row`
- No existing `@media (max-width: 1100px)` or `@media (max-width: 768px)` blocks are modified

---

## Wave 2 — HTML Structural Prep (depends on Wave 1)

Minimal additive HTML changes to support the CSS accordion grid-rows trick (Wave 3) and the SVG icon upgrade.

---

### Task 2.1 — Replace emoji drop icon with inline SVG in `index.html`

**read_first:**
- `frontend/index.html` (lines 41–47, the `.drop-zone-content` block)

**action:**
On line 42, replace the emoji `<span class="drop-icon">📄</span>` with an inline SVG that inherits `currentColor` from the parent, maintains the same `drop-icon` class for existing CSS targeting:
```html
<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="drop-icon">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
</svg>
```
The `class="drop-icon"` is preserved so the existing CSS `.drop-icon { font-size: 48px; margin-bottom: var(--space-xs); }` continues to apply. The SVG `width`/`height` attributes explicitly set the size.

**acceptance_criteria:**
- `index.html` no longer contains the text `📄`
- `index.html` contains an `<svg ... class="drop-icon">` element in `.drop-zone-content`
- The SVG has `stroke="currentColor"` and appropriate `width="48" height="48"`
- The surrounding `.drop-zone-content`, `<input>`, `.drop-text`, `.drop-or`, and `<button>` elements are untouched

---

### Task 2.2 — Wrap static accordion `.layer-body` content with `.layer-body-inner` in `index.html`

**read_first:**
- `frontend/index.html` (lines 150–155, the `#layerAccordionList` block)

**action:**
The `#layerAccordionList` div (line 152–154) is dynamically populated by JS and has no static `.layer-body` content in the HTML. The static HTML has no `.layer-card` elements to wrap. Therefore **Task 2.2 is a no-op on the static HTML** — the `.layer-body-inner` wrapper for dynamically generated cards is handled entirely in Task 5.6 (JS template).

However, if a static `.layer-body` demo structure were present in the HTML, the wrapper pattern would be:
```html
<div class="layer-body">
    <div class="layer-body-inner">
        <!-- existing content -->
    </div>
</div>
```

Since no static `.layer-body` exists in `index.html` as of the current file (all cards are JS-rendered), this task is fulfilled by Task 5.6. Mark as complete when Task 5.6 is done.

**acceptance_criteria:**
- Confirm `index.html` contains no static `.layer-body` elements that would break with the CSS grid-rows trick
- All accordion cards are confirmed to be JS-generated (confirmed: `#layerAccordionList` is populated dynamically)
- Task 5.6 handles the `.layer-body-inner` wrapper in the JS template

---

## Wave 3 — CSS Accordion Fix (depends on Wave 2)

Replace the `max-height: 500px` hack with a CSS grid-rows trick for natural auto-height accordion expansion.

---

### Task 3.1 — Update `.layer-body` to use CSS grid-rows trick in `style.css`

**read_first:**
- `frontend/style.css` (lines 667–688, the `.layer-body` and `.layer-card.open .layer-body` blocks)

**action:**
Replace the existing `.layer-body` rule (lines 667–673) and the `.layer-card.open .layer-body` rule (lines 680–684) with the CSS grid-rows approach. **Keep all other rules in the block (`.layer-card.open`, `.layer-card.open .layer-chevron`) untouched.**

Replace:
```css
.layer-body {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.35s ease, padding 0.35s ease;
    padding: 0 20px;
    border-top: 1px solid transparent;
}
```
With:
```css
.layer-body {
    display: grid;
    grid-template-rows: 0fr;
    transition: grid-template-rows 0.35s ease;
    overflow: hidden;
    border-top: 1px solid transparent;
}
```

Replace:
```css
.layer-card.open .layer-body {
    max-height: 500px;
    padding-bottom: 20px;
    border-top-color: var(--border-glow);
}
```
With:
```css
.layer-card.open .layer-body {
    grid-template-rows: 1fr;
    border-top-color: var(--border-glow);
}
```

After the `.layer-card.open .layer-body` rule, add the new inner wrapper rule:
```css
.layer-body-inner {
    min-height: 0;
    padding: 0 20px 20px;
}
```

**acceptance_criteria:**
- `.layer-body` in `style.css` contains `display: grid;` and `grid-template-rows: 0fr;`
- `.layer-body` no longer contains `max-height: 0;` or `transition: max-height`
- `.layer-card.open .layer-body` contains `grid-template-rows: 1fr;`
- `.layer-card.open .layer-body` no longer contains `max-height: 500px;` or `padding-bottom: 20px;`
- `.layer-body-inner` rule exists with `min-height: 0;` and `padding: 0 20px 20px;`
- `.layer-card.open` (border rule) and `.layer-card.open .layer-chevron` rules are untouched

---

## Wave 4 — JS Bug Fixes and Data Fixes (can run in parallel with Wave 3)

Fix three confirmed data bugs in `app.js`. These do not depend on any CSS changes.

---

### Task 4.1 — Fix `verdict_text` field in `app.js`

**read_first:**
- `frontend/app.js` (lines 482–484, the verdict assignment block inside `populateDashboardView`)

**action:**
Lines 483–484 currently read:
```javascript
const verdict = data.layer_details.verdict || "No feedback generated.";
document.getElementById("qualitativeVerdictText").textContent = data.layer_details.verdict ? (typeof data.layer_details.verdict === 'string' ? data.layer_details.verdict : JSON.stringify(data.layer_details.verdict)) : verdict;
```

Replace these two lines with:
```javascript
const verdict = data.verdict_text || data.layer_details?.verdict || "No feedback generated.";
document.getElementById("qualitativeVerdictText").textContent = verdict;
```

The fallback chain ensures: live API responses (which return `verdict_text` at top level) work correctly, AND the demo mock payload (which uses `layer_details.verdict`) continues to work.

**acceptance_criteria:**
- `app.js` line that reads verdict uses `data.verdict_text` as the primary source
- `data.layer_details?.verdict` is used as a fallback (note optional chaining `?.`)
- `"No feedback generated."` is the final fallback
- `#qualitativeVerdictText` element is still updated with `.textContent`
- No other lines in `populateDashboardView` are changed

---

### Task 4.2 — Fix citation table: remove hardcoded NLP paper titles, replace with summary row

**read_first:**
- `frontend/app.js` (lines 567–603, the "Scaffold verified sample references" block inside `populateDashboardView`)

**action:**
Remove the entire `sampleVerifiedTitles` array (lines 568–574) and the `for` loop that uses it (lines 576–602). Replace with a single summary row that uses the real `cr.verified` count:
```javascript
// Show verified count as summary row (real API data — backend returns count only, not titles)
if (cr.verified > 0) {
    const row = document.createElement("tr");
    row.className = "ref-row";

    const col1 = document.createElement("td");
    col1.className = "ref-citation-entry";
    col1.innerHTML = `<div class="tooltip">${cr.verified} citation${cr.verified > 1 ? "s" : ""} verified<span class="tooltiptext">Verified against Semantic Scholar title index and CrossRef DOI registry.</span></div>`;
    row.appendChild(col1);

    const col2 = document.createElement("td");
    col2.className = "font-mono";
    col2.textContent = "Semantic Scholar";
    row.appendChild(col2);

    const col3 = document.createElement("td");
    col3.innerHTML = `<span class="ref-badge success">VERIFIED</span>`;
    row.appendChild(col3);

    const col4 = document.createElement("td");
    col4.textContent = "Citations successfully matched in reference libraries.";
    row.appendChild(col4);

    tableBody.appendChild(row);
}
```

**acceptance_criteria:**
- `app.js` no longer contains the `sampleVerifiedTitles` array (no "Vaswani", "Devlin", "Brown", "Sutskever", "Bahdanau" hardcoded strings)
- A verified summary row IS added when `cr.verified > 0` using `cr.verified` count
- Summary row uses `class="ref-badge success"` and `"Semantic Scholar"` method column
- Flagged items loop (`cr.flagged_items.forEach`) and flagged DOIs loop (`cr.flagged_dois.forEach`) are untouched

---

### Task 4.3 — Fix grade recommendation badge: switch to grade-letter-based logic

**read_first:**
- `frontend/app.js` (lines 295–317, the "Semantic colors setup" block inside `populateDashboardView`)

**action:**
The existing score-threshold logic (lines 296–316) uses `targetScore >= 85`, `>= 70`, etc. Replace the entire `colorClass`/`recText` block with grade-letter-based logic. The `badge.textContent = data.grade;` assignment (line 293) and `circle.style.stroke = colorClass;` / `rec.style.color = colorClass;` / `rec.style.backgroundColor` / `rec.textContent = recText;` assignments (lines 313–317) at the bottom should still exist.

Replace lines 296–317 with:
```javascript
// Grade-letter-based recommendation mapping (per STITCH_FRONTEND_SPEC §1.2.1)
const gradeLetter = data.grade ? data.grade.charAt(0).toUpperCase() : "F";
let colorClass = "var(--accent-danger)";
let recText = "NOT READY FOR SUBMISSION";

if (gradeLetter === "A" || gradeLetter === "B") {
    colorClass = "var(--accent-success)";
    recText = "RECOMMENDED FOR JOURNAL SUBMISSION";
} else if (gradeLetter === "C") {
    colorClass = "var(--accent-warning)";
    recText = "MINOR REVISIONS REQUIRED";
} else if (gradeLetter === "D") {
    colorClass = "var(--accent-danger)";
    recText = "SIGNIFICANT REVISIONS REQUIRED";
}

circle.style.stroke = colorClass;
badge.style.color = colorClass;
rec.style.color = colorClass;
rec.style.backgroundColor = `rgba(${colorClass === "var(--accent-success)" ? "16, 185, 129" : colorClass === "var(--accent-warning)" ? "245, 158, 11" : "239, 68, 68"}, 0.12)`;
rec.textContent = recText;
```

**Note:** The `circle.style.stroke = colorClass` line now sets the gauge stroke to the grade-based color. Task 5.2 will **additionally** set the stroke to score-range colors (overriding this for the gauge only). Task 4.3 sets the badge/rec colors by grade; Task 5.2 will handle the gauge stroke independently.

**acceptance_criteria:**
- `app.js` grade recommendation logic uses `data.grade.charAt(0)` not `targetScore >= N` comparisons
- A/B grade → `"RECOMMENDED FOR JOURNAL SUBMISSION"` with success color
- C grade → `"MINOR REVISIONS REQUIRED"` with warning color
- D grade → `"SIGNIFICANT REVISIONS REQUIRED"` with danger color
- F/other → `"NOT READY FOR SUBMISSION"` with danger color
- `rec.textContent` and `rec.style` assignments remain present

---

## Wave 5 — JS Enhancements (depends on Wave 1 CSS being done)

Six JS enhancements that add animations, visual polish, and correct data binding.

---

### Task 5.1 — Add score counter ticker animation function in `app.js`

**read_first:**
- `frontend/app.js` (lines 274–290, the start of `populateDashboardView` up to gauge animation)

**action:**
Define a new `animateScore` function. Add it **above** `populateDashboardView` (e.g., after the `showToastNotification` function at line 137 or immediately before `populateDashboardView` at line 274):
```javascript
// Score counter ticker — counts from 0 to targetScore over ~1.8s
function animateScore(targetScore) {
    const el = document.getElementById("gaugeScoreText");
    if (!el) return;
    let count = 0;
    const steps = Math.max(Math.round(targetScore), 1);
    const stepDuration = 1800 / steps;
    const timer = setInterval(() => {
        count++;
        el.textContent = count;
        if (count >= steps) {
            el.textContent = Math.round(targetScore);
            clearInterval(timer);
        }
    }, stepDuration);
}
```

Then, inside `populateDashboardView`, replace line 280:
```javascript
document.getElementById("gaugeScoreText").textContent = targetScore;
```
With:
```javascript
animateScore(targetScore);
```

This removes the instant score set and replaces it with the animated count-up.

**acceptance_criteria:**
- `app.js` contains a function `animateScore(targetScore)` using `setInterval`
- `animateScore` updates `#gaugeScoreText` incrementally from 0 to `Math.round(targetScore)` over approximately 1800ms
- `animateScore` is called from `populateDashboardView` in place of the direct `.textContent = targetScore` assignment
- The existing gauge SVG offset animation (`circle.style.strokeDashoffset = offset`) is untouched

---

### Task 5.2 — Add gauge stroke color ranges based on score in `app.js`

**read_first:**
- `frontend/app.js` (lines 282–313, the gauge animation block and colorClass assignment in `populateDashboardView`)

**action:**
After the gauge SVG offset animation lines (after `circle.style.strokeDashoffset = offset;`, around line 288), add score-range gauge stroke color logic that overrides whatever color Task 4.3 set on `circle.style.stroke`:
```javascript
// Score-range gauge stroke color (independent of grade badge color)
let gaugeStrokeColor;
if (targetScore >= 85) {
    gaugeStrokeColor = "#10B981";   // emerald — A grade territory
} else if (targetScore >= 70) {
    gaugeStrokeColor = "#06b6d4";   // cyan — B grade territory
} else if (targetScore >= 55) {
    gaugeStrokeColor = "#F59E0B";   // amber — C grade territory
} else {
    gaugeStrokeColor = "#EF4444";   // red — D/F grade territory
}
circle.style.stroke = gaugeStrokeColor;
```

This code should be placed **after** the Task 4.3 `circle.style.stroke = colorClass;` line so that score-range colors always win for the gauge, while the badge/rec colors are controlled by grade letter.

**acceptance_criteria:**
- `app.js` contains score-range color logic with thresholds `>= 85`, `>= 70`, `>= 55`, `< 55`
- Score ≥ 85 → `circle.style.stroke = "#10B981"` (emerald)
- Score 70–84 → `circle.style.stroke = "#06b6d4"` (cyan)
- Score 55–69 → `circle.style.stroke = "#F59E0B"` (amber)
- Score < 55 → `circle.style.stroke = "#EF4444"` (red)
- `circle` still refers to `document.getElementById("gaugeCircle")`

---

### Task 5.3 — Add layer weight labels to accordion card headers in `app.js`

**read_first:**
- `frontend/app.js` (lines 350–406, the `activeLayers` array and header-building block inside `populateDashboardView`)

**action:**
**Step A:** Update the `activeLayers` array (lines 350–356) to include a `weight` field for each layer:
```javascript
const activeLayers = [
    { key: "structure_sections", label: "Structure & Sections", num: "01", weight: "20%" },
    { key: "clarity_writing",    label: "Clarity & Writing",    num: "02", weight: "25%" },
    { key: "methodology_rigor",  label: "Methodology Rigor",    num: "03", weight: "25%" },
    { key: "evidence_claims",    label: "Evidence & Claims",    num: "04", weight: "20%" },
    { key: "citations",          label: "Citations & References", num: "05", weight: "10%" }
];
```

**Step B:** In the `metaBlock` construction block (around lines 393–406), after appending `scoreSpan` to `metaBlock`, add a weight chip:
```javascript
const weightSpan = document.createElement("span");
weightSpan.className = "layer-weight";
weightSpan.textContent = layer.weight;
metaBlock.appendChild(weightSpan);
metaBlock.appendChild(scoreSpan);  // reorder: weight BEFORE score, both BEFORE chevron
metaBlock.appendChild(chevron);
```

Note: The current code does `metaBlock.appendChild(scoreSpan); metaBlock.appendChild(chevron);`. Change this so the weight chip appears between the title and the score, by updating the append order. The final order in `metaBlock` should be: `weightSpan` → `scoreSpan` → `chevron`.

**acceptance_criteria:**
- `activeLayers` array in `app.js` has a `weight` field on every entry with values `"20%"`, `"25%"`, `"25%"`, `"20%"`, `"10%"` respectively
- Each generated accordion `.layer-header` contains a `<span class="layer-weight">` element with the correct percentage
- `layer-weight` span appears in the meta block alongside the score

---

### Task 5.4 — Add grade badge class assignment in `app.js`

**read_first:**
- `frontend/app.js` (lines 291–294, the `badge` element and `badge.textContent = data.grade` assignment)

**action:**
After `badge.textContent = data.grade;` (line 293), add grade class assignment. First, remove any previously assigned grade letter classes to avoid accumulation on `resetUploadView` / re-render:
```javascript
badge.textContent = data.grade;
// Assign grade-letter class for CSS color coding (remove any previous grade class first)
badge.classList.remove("grade-a", "grade-b", "grade-c", "grade-d", "grade-f");
const gradeLetter = data.grade ? data.grade.charAt(0).toLowerCase() : "f";
badge.classList.add(`grade-${gradeLetter}`);
```

The `gradeLetter` variable extracted here is also used by Task 4.3 — coordinate so both tasks use consistent variable naming (both extract `data.grade.charAt(0)`).

**acceptance_criteria:**
- After `populateDashboardView` runs, `#gradeBadge` element has exactly one `grade-*` class (`grade-a`, `grade-b`, `grade-c`, `grade-d`, or `grade-f`)
- The class is derived from the first character of `data.grade` (case-insensitive)
- `badge.classList.remove(...)` is called before `add` to prevent stale classes on re-render
- `badge.textContent` is still set to `data.grade`

---

### Task 5.5 — Add score=0 failover toast in `app.js`

**read_first:**
- `frontend/app.js` (lines 274–604, the full `populateDashboardView` function)

**action:**
At the **end** of `populateDashboardView`, after the reference table body is built (after line 603, before the closing `}`), add:
```javascript
// Score=0 failover — warn user if Gemini returned no score (likely quota exhausted)
if (data.final_score === 0.0) {
    showToastNotification("⚠ Gemini returned a score of 0 — API quota may be exhausted. Try the sample demo.", false);
}
```

**acceptance_criteria:**
- `app.js` `populateDashboardView` ends with a `final_score === 0.0` check
- If true, `showToastNotification` is called with the quota exhaustion message
- `showToastNotification` is called with `false` as the second arg (error toast, not success)
- No other code paths or logic are changed

---

### Task 5.6 — Add `.layer-body-inner` wrapper to JS-generated accordion cards in `app.js`

**read_first:**
- `frontend/app.js` (lines 411–479, the card body building block — `const body`, `splitDiv`, column construction, `body.appendChild(splitDiv)`)

**action:**
The CSS grid-rows accordion trick (Task 3.1) requires each `.layer-body` to have exactly one direct child element (`.layer-body-inner`) with `min-height: 0`. Currently the JS builds `.layer-body` and appends `.layer-content-split` directly to it.

**Step A:** After creating `body` (the `.layer-body` div, around line 412), create an inner wrapper:
```javascript
const body = document.createElement("div");
body.className = "layer-body";

// Inner wrapper required for CSS grid-rows accordion animation
const bodyInner = document.createElement("div");
bodyInner.className = "layer-body-inner";

// Prevent click inside body collapsing the card
body.addEventListener("click", (e) => {
    e.stopPropagation();
});
```

**Step B:** Append `splitDiv` to `bodyInner` (not to `body`) and append `bodyInner` to `body`:
```javascript
// was: body.appendChild(splitDiv);
// now:
bodyInner.appendChild(splitDiv);
body.appendChild(bodyInner);
```

**acceptance_criteria:**
- JS-generated accordion cards have DOM structure: `.layer-body > .layer-body-inner > .layer-content-split`
- `.layer-body` has the `click` stopPropagation listener (unchanged from existing code, just moved/kept)
- `.layer-body-inner` div has `class="layer-body-inner"` 
- All issue/suggestion list content remains inside `.layer-content-split` > `.layer-body-inner` > `.layer-body`
- Accordion open/close still works (confirmed by `card.classList.toggle("open")` on card click)

---

## Execution Order

```
Wave 1 (1.1 → 1.7 in any order within wave, all must complete before Wave 2+)
    ↓
Wave 2 (2.1, 2.2 in any order — both inform Wave 3)
    ↓
Wave 3 (3.1 — depends on 2.2 confirming no static .layer-body to break)
    ║
Wave 4 (4.1, 4.2, 4.3 — can run in parallel with Wave 3; JS-only)
    ↓
Wave 5 (5.1 → 5.6 — all depend on Wave 1 CSS vars; 5.6 coordinates with 3.1)
```

Wave 4 tasks are independent of CSS and can begin as soon as Wave 1 completes.
Wave 5 tasks depend on Wave 1 (CSS variables referenced by class names added in JS).
Task 5.2 should be placed **after** Task 4.3 code within `populateDashboardView` (the gauge stroke color must win over the grade badge color for the gauge element).

---

## Verification Checklist

Manual checks to confirm each improvement works after implementation:

### CSS Variable Fixes
- [ ] Open browser DevTools → Computed Styles on `.drop-zone` — padding should show `48px` (not `0`)
- [ ] Hover over a `.layer-card` — should transition smoothly (previously static with no animation)
- [ ] Check `--space-2xl` and `--transition-smooth` appear in the `:root` computed styles panel

### Body Gradient
- [ ] Load the app — background should show a subtle lighter radial ellipse in the upper-left area of the deep navy background

### Stepper Glow
- [ ] Upload a PDF or click "Try Pre-Cached Sample Paper" — the active step icon (●) should have a soft cyan glow (`box-shadow`)

### Score Gauge
- [ ] Run demo mode — gauge stroke should be **cyan** `#06b6d4` for the demo score of 77 (B grade territory)
- [ ] Verify score text in gauge counts up from 0 to 77 over ~1.8 seconds instead of jumping directly to 77

### Grade Badge
- [ ] Demo mode grade is "B — Good" — `#gradeBadge` element should have class `grade-b` in DOM inspector
- [ ] Badge should show a blue-tinted gradient background (not the flat dark `--bg-raised`)

### Recommendation Badge
- [ ] Demo mode grade "B" → rec badge text should read "RECOMMENDED FOR JOURNAL SUBMISSION" (emerald green)
- [ ] If demo data were changed to grade "C" → rec badge text should read "MINOR REVISIONS REQUIRED" (amber)

### Layer Accordion Headers
- [ ] Expand dashboard after demo — each layer card header should show a weight chip (e.g., "25%" for Clarity & Writing)
- [ ] Layer weight chip should use JetBrains Mono font and appear as a small pill between the title and score

### Accordion Expansion
- [ ] Click a layer card to expand — it should expand to its **natural content height** (not capped at 500px)
- [ ] A layer with many issues should fully expand without truncation
- [ ] Expand/collapse transition should be smooth (0.35s ease)

### Verdict Text
- [ ] Demo mode uses `layer_details.verdict` — verify verdict card shows the correct multi-sentence verdict text
- [ ] Live API mode: verify verdict card shows `data.verdict_text` (not blank/undefined)

### Citation Table
- [ ] Demo mode: table should show 1 DUPLICATE row (Vaswani duplicate), 1 INVALID DOI row (fake-doi-1), and 1 VERIFIED summary row ("6 citations verified" — using `cr.verified = 6`)
- [ ] Table should NOT show any hardcoded "Devlin et al.", "Brown et al." etc. title rows

### Drop Zone Icon
- [ ] Upload zone icon renders as a crisp SVG document outline (not pixelated emoji 📄)
- [ ] SVG uses `currentColor` and inherits the existing icon color

### 480px Breakpoint
- [ ] Resize browser to 400px width — cite-metrics row should stack vertically
- [ ] Grade row should stack vertically at 400px width

### Score=0 Failover
- [ ] To test: temporarily set `data.final_score = 0.0` in demo payload — a warning toast should appear after dashboard renders
- [ ] Toast message: "⚠ Gemini returned a score of 0 — API quota may be exhausted. Try the sample demo."

### No Regressions
- [ ] All 5 accordion cards expand and collapse correctly
- [ ] "Try Pre-Cached Sample Paper" button still triggers demo mode
- [ ] "Upload New Paper" button resets view correctly
- [ ] PDF download button still appears in verdict card footer
- [ ] Toast notifications still slide in/out for both success and error states
- [ ] Health check dot still updates on page load
- [ ] Section pills render correctly with present/missing states

---

*Plan authored: 2026-06-11*  
*Phase: 11 — Improve the Frontend UI*  
*Executor: Autonomous (all tasks are concrete, additive-only, with exact line references)*
