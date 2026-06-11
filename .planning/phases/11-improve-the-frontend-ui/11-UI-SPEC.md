# Phase 11: Improve the Frontend UI — UI Design Contract

**Gathered:** 2026-06-11
**Status:** Ready for planning
**Source:** Inline from Phase 11 RESEARCH.md

---

## Guiding Principle

> **ADDITIVE ONLY** — No existing UI elements are removed. Every improvement adds to or enhances what is already there. The dashboard, upload view, stepper, gauge, accordion layers, citation table, verdict card, and all badges remain. Only visual quality and correctness are improved.

---

## 1. Color & Theming

### 1.1 Existing Token System (Preserved Exactly)
```css
--bg-base:           #0a0e17
--bg-surface:        hsla(223, 47%, 16%, 0.55)
--bg-raised:         hsla(223, 47%, 20%, 0.7)
--backdrop-blur:     blur(14px)
--accent-data:       #00E5FF
--accent-success:    #10B981
--accent-warning:    #F59E0B
--accent-danger:     #EF4444
--accent-info:       #3B82F6
--card-radius:       16px
--border-subtle:     hsla(223, 47%, 40%, 0.25)
```

### 1.2 New: Body Radial Gradient (ADD to body)
```css
body {
  background: radial-gradient(
    ellipse at 30% 20%,
    hsla(223, 60%, 18%, 0.8) 0%,
    var(--bg-base) 65%
  );
  min-height: 100vh;
}
```
Adds atmospheric depth without changing the base color.

### 1.3 New: Grade-Based Color Classes for `.grade-badge`
Applied dynamically via JS. Add these CSS classes:

| Class | Background | Border | Text |
|-------|-----------|--------|------|
| `.grade-badge.grade-a` | `rgba(16,185,129,0.15)` | `rgba(16,185,129,0.4)` | `#10B981` |
| `.grade-badge.grade-b` | `rgba(59,130,246,0.15)` | `rgba(59,130,246,0.4)` | `#60a5fa` |
| `.grade-badge.grade-c` | `rgba(245,158,11,0.15)` | `rgba(245,158,11,0.4)` | `#F59E0B` |
| `.grade-badge.grade-d` | `rgba(239,68,68,0.15)` | `rgba(239,68,68,0.4)` | `#EF4444` |
| `.grade-badge.grade-f` | `rgba(239,68,68,0.15)` | `rgba(239,68,68,0.4)` | `#EF4444` |

### 1.4 New: Gauge Stroke Color Ranges
Score-based stroke color applied via JS (replaces single static green):

| Score Range | Color | Token |
|------------|-------|-------|
| ≥ 85 | Emerald | `#10B981` |
| 70 – 84 | Cyan-blue | `#06b6d4` |
| 55 – 69 | Amber | `#F59E0B` |
| < 55 | Red | `#EF4444` |

### 1.5 New: UNREACHABLE Citation Badge Color
Add `.ref-badge.unreachable { background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }` — amber tone, distinct from INVALID (red) and DUPLICATE (orange-red).

---

## 2. Typography

### 2.1 Existing Font Stack (Preserved)
```
Font UI:      Inter (Google Fonts)
Font Header:  Outfit (Google Fonts)
Font Data:    JetBrains Mono (Google Fonts)
```
**No font changes.**

### 2.2 New: Layer Weight Chip Typography
```css
.layer-weight {
  font-family: var(--font-data);   /* JetBrains Mono */
  font-size: 11px;
  letter-spacing: 0.03em;
  color: #64748b;
}
```

### 2.3 Score Gauge Text
Score display element (`#gaugeScoreText`) keeps existing size. The ticker animation counts up numerically — no font change needed.

---

## 3. Layout & Spacing

### 3.1 Bug Fix: Add Missing CSS Variables to `:root`
```css
--space-2xl:          48px;    /* FIX: was undefined, used in drop zone + stepper */
--transition-smooth:  all 0.25s cubic-bezier(0.4, 0, 0.2, 1);  /* FIX: was undefined, used in layer-card */
```
These are not visual changes — they fix broken padding that currently falls back to 0.

### 3.2 Accordion: Switch to CSS Grid-Rows Auto-Height
Replace `max-height: 500px` approach with CSS grid-rows trick so accordions expand to their natural height:

```css
/* Replace existing .layer-body rules */
.layer-body {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.35s ease;
  overflow: hidden;
  /* Keep existing padding on the inner wrapper, not here */
}
.layer-body-inner {
  min-height: 0;
  padding: 0 20px 20px;  /* inner padding preserved */
}
.layer-card.open .layer-body {
  grid-template-rows: 1fr;
}
```

HTML change: wrap content of `.layer-body` in `<div class="layer-body-inner">`.

### 3.3 New: 480px Mobile Breakpoint (additive)
```css
@media (max-width: 480px) {
  .sections-grid { grid-template-columns: 1fr; }
  .ref-table-wrap { overflow-x: auto; }
  .cite-metrics { flex-direction: column; gap: 8px; }
  .grade-row { flex-direction: column; align-items: flex-start; gap: 12px; }
}
```
Adds a third breakpoint below the existing 768px one. No existing breakpoints modified.

---

## 4. Component Specs

### 4.1 Drop Zone (`.drop-zone`)
- **Change:** Apply the now-defined `--space-2xl` variable (was broken, padding was 0)
- **Visual result:** Drop zone gets proper 48px padding — looks spacious and correct
- **Icon:** Replace emoji `📄` with inline SVG document icon (crisp on HiDPI):
```html
<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="drop-icon">
  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
  <polyline points="14 2 14 8 20 8"/>
  <line x1="16" y1="13" x2="8" y2="13"/>
  <line x1="16" y1="17" x2="8" y2="17"/>
  <polyline points="10 9 9 9 8 9"/>
</svg>
```

### 4.2 Stepper (`.stepper`)
- **Change:** Add glow to active step icon
```css
.step.active .step-icon {
  color: var(--accent-data);
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.5);
  border-radius: 50%;
  padding: 2px;
}
```
- **No structural changes** — existing step HTML preserved

### 4.3 Score Gauge (`.gauge-svg`)
- **Stroke color:** Set dynamically based on score range (see §1.4)
- **Score ticker:** The `#gaugeScoreText` element animates from 0 → final_score over 1.8s
- **No structural changes to SVG**

### 4.4 Grade Badge (`.grade-badge`)
- **Change:** JS assigns class `grade-a`, `grade-b`, `grade-c`, `grade-d`, or `grade-f` based on first letter of `data.grade`
- **CSS:** Grade-specific gradient background + border (see §1.3)
- **Existing badge element and text preserved**

### 4.5 Layer Accordion Cards (`.layer-card`)
Each layer card header gets a weight chip added (after existing score display):
```html
<!-- Added INSIDE existing .layer-meta, after score span -->
<span class="layer-weight">20%</span>
```
Weight values per layer:
- `structure_sections` → 20%
- `clarity_writing` → 25%
- `methodology_rigor` → 25%
- `evidence_claims` → 20%
- `citations` → 10%

Accordion expand uses CSS grid-rows (see §3.2). **All existing accordion content preserved.**

### 4.6 Verdict Card (`.verdict-card`)
- **Bug fix:** JS reads `data.verdict_text` (top-level) with fallback to `data.layer_details?.verdict`
- **No visual changes** — existing card structure preserved

### 4.7 Citation Section
**Citation Metrics Row** (`.cite-metrics`) — unchanged.

**Reference Table** — existing structure preserved, with these data changes:
- **Flagged items** (`flagged_items` array): render first, DUPLICATE badge — real data ✓
- **Flagged DOIs** (`flagged_dois` array): render second, INVALID badge — real data ✓  
- **Unreachable** (from `citation_result.unreachable`): UNREACHABLE badge (amber) if count > 0
- **Verified summary row** (NEW): replace hardcoded NLP paper titles with:
  ```html
  <tr class="ref-row verified-summary">
    <td colspan="3">
      <span class="ref-badge verified">VERIFIED</span>
      <span class="ref-title">X citations verified via Semantic Scholar</span>
    </td>
  </tr>
  ```
  Where X = `citation_result.verified`
- **Hardcoded sample titles removed** (Vaswani, Devlin, Brown array deleted)

### 4.8 Grade Recommendation Badge (`.rec-badge`)
- **Change:** Switch from score-threshold logic to grade-letter logic:
  - `A` or `B` → "RECOMMENDED FOR JOURNAL SUBMISSION" (emerald)
  - `C` → "MINOR REVISIONS REQUIRED" (amber)
  - `D` → "SIGNIFICANT REVISIONS REQUIRED" (red)
  - `F` → "NOT READY FOR SUBMISSION" (red)
- **Badge element preserved** — only the text and color logic changes

### 4.9 Failover: Score = 0
When `data.final_score === 0.0`, show an additional toast:
```
⚠ Gemini returned a score of 0 — API quota may be exhausted. Try the sample demo.
```
No structural changes — uses existing toast system.

---

## 5. Interaction & Animation

### 5.1 Score Counter Ticker
```javascript
function animateScore(targetScore) {
    const el = document.getElementById("gaugeScoreText");
    let count = 0;
    const steps = Math.round(targetScore);
    const stepDuration = 1800 / Math.max(steps, 1);
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
Called alongside existing gauge animation when dashboard renders.

### 5.2 Accordion Expand Animation
CSS grid-rows: `0fr → 1fr` over `0.35s ease`. Smoother than max-height and supports auto-height content.

### 5.3 Stepper Glow (Active State)
`box-shadow: 0 0 12px rgba(0,229,255,0.5)` on `.step.active .step-icon`. Existing pulse animation preserved alongside.

### 5.4 Body Gradient
Static — no animation. Adds depth to the background.

---

## 6. Accessibility & Responsiveness

### 6.1 Existing Breakpoints (Unchanged)
- 1100px — panel layout switch
- 768px — mobile stack

### 6.2 New 480px Breakpoint (Additive)
- Section pills grid: 2 columns → 1 column
- Citation metrics row: flex → column
- Reference table: add horizontal scroll wrapper
- Grade row: flex → column stack

### 6.3 Tooltip Accessibility
Existing `title` attributes on reference table rows preserved. No new ARIA changes needed.

### 6.4 SVG Drop Icon
Inline SVG uses `currentColor` (inherits from parent) — respects any contrast-mode overrides.

---

## Artifacts This Phase Produces

**Modified files:**
- `frontend/style.css` — new CSS vars, body gradient, grade badge classes, layer-weight chip, accordion grid-rows, stepper glow, ref-badge.unreachable, 480px breakpoint
- `frontend/app.js` — score ticker, grade badge class assignment, gauge color ranges, weight labels in layer headers, grade-based rec badge logic, verdict_text fix, citation table data fix, score=0 failover
- `frontend/index.html` — SVG drop icon, `.layer-body-inner` wrapper div

**No new files created. No backend changes.**

---

## UI-SPEC COMPLETE
