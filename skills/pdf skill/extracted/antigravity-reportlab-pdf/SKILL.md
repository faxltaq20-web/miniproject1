---
name: antigravity-reportlab-pdf
description: >
  Use this skill whenever generating or improving PDF reports for the Antigravity / ResearchSense project
  using Python and ReportLab's PLATYPUS engine. Covers: creating the full report layout (cover page,
  score hero, parameter breakdown grid, citation analysis, verdict), defining custom Flowables for
  design elements that PLATYPUS cannot produce natively (progress bars, score circles, dark cards,
  section headers), using Canvas callbacks for full-bleed cover pages, and wiring everything together
  with BaseDocTemplate + PageTemplate. Trigger on any task involving report_generator.py, PDF styling,
  adding new sections, fixing layout bugs, or changing the visual theme of the ResearchSense report.
---

# Antigravity ReportLab PDF — Skill Guide

## Architecture Decision: PLATYPUS Hybrid (not pure Canvas)

**Always use PLATYPUS + custom Flowables. Never rewrite to pure Canvas.**

| Concern | PLATYPUS Hybrid | Pure Canvas |
|---|---|---|
| Page breaks with variable content | ✅ Automatic | ❌ Manual Y math |
| Variable issues/suggestions per param | ✅ Just add flowables | ❌ Overflow breaks layout |
| Cover page (full-bleed dark bg) | ✅ `onPage` Canvas callback | ✅ Native |
| Rounded cards, progress bars | ✅ Custom Flowable (Canvas draw) | ✅ Native |
| Code complexity | ✅ Low — story list | ❌ High — coordinate tracking |
| **Verdict** | **Use this** | **Don't use this** |

The correct pattern is **PLATYPUS for flow + Canvas drawing inside custom Flowables for styled components**.

---

## Project Stack

```
report_generator.py
  └─ ReportLab 4.x (pip install reportlab)
       ├─ BaseDocTemplate        — document container with page templates
       ├─ PageTemplate           — defines frames + onPage callbacks
       ├─ Frame                  — rectangular text area on a page
       ├─ PLATYPUS story list    — [Flowable, Flowable, ...] → auto-paginated
       └─ Custom Flowables       — Canvas drawing for styled components
```

---

## Color Tokens

Define once at the top of `report_generator.py`. **Never hardcode hex values in component code.**

```python
from reportlab.lib.colors import HexColor, white

C_PRIMARY  = HexColor('#0F1B35')   # dark navy — backgrounds, headings
C_ACCENT   = HexColor('#4F8EF7')   # blue — borders, highlights, pills
C_ACCENT2  = HexColor('#7C3AED')   # purple — gradient bar, decorative
C_WARNING  = HexColor('#F59E0B')   # amber — medium score bars & borders
C_SUCCESS  = HexColor('#10B981')   # green — verified DOIs, fix labels
C_DANGER   = HexColor('#EF4444')   # red — issues, unverified DOIs
C_LIGHT    = HexColor('#F0F4FF')   # light blue-grey — card backgrounds
C_TEXT     = HexColor('#1E293B')   # near-black — body text
C_MUTED    = HexColor('#64748B')   # grey — subtitles, labels
C_BORDER   = HexColor('#E2E8F0')   # light grey — dividers, box borders
```

---

## ParagraphStyle Helper

```python
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

def S(name, **kw):
    """Create a ParagraphStyle with sensible defaults."""
    defaults = dict(
        fontName='Helvetica', fontSize=10,
        textColor=C_TEXT, leading=14,
        spaceAfter=0, spaceBefore=0,
    )
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)
```

Usage examples:
```python
S('body')                                          # default body text
S('label', fontSize=7, textColor=C_MUTED)         # small muted label
S('heading', fontName='Helvetica-Bold', fontSize=14, textColor=C_PRIMARY)
S('centered', alignment=TA_CENTER)
S('mono', fontName='Courier', fontSize=9)          # DOI / code text
```

---

## Document Setup

```python
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, NextPageTemplate, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io

W, H = A4
MARGIN_H = 18 * mm   # left/right
MARGIN_T = 14 * mm   # top
MARGIN_B = 16 * mm   # bottom (space for footer)
AVAIL_W  = W - 2 * MARGIN_H

def build_pdf(report_data: dict) -> bytes:
    buf = io.BytesIO()

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN_H, rightMargin=MARGIN_H,
        topMargin=MARGIN_T,  bottomMargin=MARGIN_B,
    )

    content_frame = Frame(
        MARGIN_H, MARGIN_B, AVAIL_W, H - MARGIN_T - MARGIN_B,
        id='main', showBoundary=0,
    )

    doc.addPageTemplates([
        PageTemplate(id='cover',   frames=[Frame(0, 0, W, H, id='cf')], onPage=draw_cover),
        PageTemplate(id='content', frames=[content_frame], onPage=draw_footer),
    ])

    story = build_story(report_data)
    doc.build([NextPageTemplate('content'), PageBreak()] + story)
    return buf.getvalue()
```

---

## Cover Page (`onPage` Canvas callback)

The cover is **100% Canvas** drawn in the `onPage` callback — no PLATYPUS flowables.
The first PageTemplate uses a full-page frame so PLATYPUS doesn't fight with it.

```python
def draw_cover(canvas, doc):
    canvas.saveState()

    # 1. Dark background
    canvas.setFillColor(C_PRIMARY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # 2. Decorative background circles (subtle, low alpha)
    for (x, y, r, col, a) in [
        (W + 50, H + 50, 170, C_ACCENT,  0.07),
        (-50,    100,    120, C_ACCENT2, 0.06),
        (W - 50, 220,    70,  C_ACCENT,  0.05),
    ]:
        canvas.setFillAlpha(a)
        canvas.setFillColor(col)
        canvas.circle(x, y, r, fill=1, stroke=0)
    canvas.setFillAlpha(1)

    # 3. Top gradient bar (split blue → purple)
    canvas.setFillColor(C_ACCENT);  canvas.rect(0,    H - 4, W * 0.55, 4, fill=1, stroke=0)
    canvas.setFillColor(C_ACCENT2); canvas.rect(W * 0.45, H - 4, W * 0.55, 4, fill=1, stroke=0)

    # 4. Brand name row
    canvas.setFillColor(C_ACCENT)
    canvas.circle(36, H - 52, 5, fill=1, stroke=0)           # brand dot
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(48, H - 57, 'RESEARCHSENSE')

    # 5. AI tag pill
    canvas.setFillColor(HexColor('#1a2d5a'))
    canvas.roundRect(36, H - 112, 120, 18, 9, fill=1, stroke=0)
    canvas.setFillColor(C_ACCENT)
    canvas.setFont('Helvetica-Bold', 7)
    canvas.drawString(48, H - 106, 'AI-POWERED ANALYSIS')

    # 6. Main title
    canvas.setFillColor(white)
    canvas.setFont('Helvetica-Bold', 36)
    canvas.drawString(36, H - 162, 'Research Paper')
    canvas.setFillColor(C_ACCENT)
    canvas.drawString(36, H - 202, 'Analysis Report')

    # 7. Accent divider
    canvas.setFillColor(C_ACCENT)
    canvas.roundRect(36, H - 218, 40, 3, 1, fill=1, stroke=0)

    # 8. Metadata grid (2 columns × 2 rows)
    canvas.setStrokeColor(HexColor('#1e3a6e'))
    canvas.setLineWidth(0.5)
    canvas.line(36, H - 238, W - 36, H - 238)

    meta = [
        ('PAPER',      doc.report_data.get('paper_name', 'paper.pdf')),
        ('ANALYSED',   doc.report_data.get('analysed_at', '')),
        ('PARAMETERS', f"{len(doc.report_data.get('parameters', []))} Dimensions"),
        ('STATUS',     doc.report_data.get('status', '')),
    ]
    for i, (label, value) in enumerate(meta):
        x = 36 + (i % 2) * 255
        y = H - 265 - (i // 2) * 36
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(HexColor('#4a6080'))
        canvas.drawString(x, y + 14, label)
        canvas.setFont('Helvetica', 10)
        canvas.setFillColor(HexColor('#ccdcee'))
        canvas.drawString(x, y, value)

    # 9. Score badge circle (bottom-right)
    bx, by = W - 72, 72
    canvas.setFillColor(HexColor('#1a2d5a'))
    canvas.setStrokeColor(C_ACCENT)
    canvas.setLineWidth(2)
    canvas.circle(bx, by, 52, fill=1, stroke=1)
    canvas.setFillColor(white)
    canvas.setFont('Helvetica-Bold', 24)
    canvas.drawCentredString(bx, by + 8, str(doc.report_data['score']))
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(HexColor('#94A3B8'))
    canvas.drawCentredString(bx, by - 6, f"/ {doc.report_data['max_score']}")
    canvas.setFillColor(C_ACCENT)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(bx, by - 22, f"Grade {doc.report_data['grade']}")

    canvas.restoreState()
```

> **Passing data to the callback:** attach `report_data` as an attribute on `doc` before building:
> ```python
> doc.report_data = report_data
> doc.build(...)
> ```

---

## Footer (`onPage` for content pages)

```python
def draw_footer(canvas, doc):
    if doc.page > 1:   # skip cover
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(HexColor('#94A3B8'))
        canvas.drawCentredString(
            W / 2, 10 * mm,
            f"ResearchSense  ·  Analysis Report  ·  Page {doc.page}"
        )
        canvas.restoreState()
```

---

## Custom Flowables

All styled components that PLATYPUS can't produce natively are implemented as `Flowable` subclasses. They use Canvas drawing inside `draw()` and tell PLATYPUS how much space they need via `wrap()`.

### Pattern

```python
from reportlab.platypus import Flowable

class MyComponent(Flowable):
    def __init__(self, ...):
        super().__init__()      # always call super
        # store params; set self._h (estimated height)

    def wrap(self, availWidth, availHeight):
        self._w = availWidth    # capture available width
        return self._w, self._h # return (width, height) consumed

    def draw(self):
        c = self.canv           # Canvas object
        # draw at (0,0) in local coordinates; (0,0) = bottom-left of flowable
```

### ProgressBar

```python
class ProgressBar(Flowable):
    """Thin horizontal bar showing score percentage."""
    def __init__(self, pct: float, color=C_WARNING, height: int = 5):
        super().__init__()
        self._pct = min(max(pct, 0), 1)
        self._color = color
        self._h = height + 4   # +4 for vertical padding

    def wrap(self, aW, aH):
        self._w = aW
        return aW, self._h

    def draw(self):
        c = self.canv
        bar_h = self._h - 4
        # Track (background)
        c.setFillColor(C_BORDER)
        c.roundRect(0, 2, self._w, bar_h, 2, fill=1, stroke=0)
        # Fill
        c.setFillColor(self._color)
        c.roundRect(0, 2, max(4, self._w * self._pct), bar_h, 2, fill=1, stroke=0)
```

### ScoreHero

```python
class ScoreHero(Flowable):
    """Dark navy card: circular score + grade pill + label + description."""
    def __init__(self, score, max_score, grade_label, title, description):
        super().__init__()
        self._score = score
        self._max   = max_score
        self._grade = grade_label   # e.g. "Grade B · Good"
        self._title = title         # e.g. "Good Overall Quality"
        self._desc  = description   # newline-separated lines
        self._h     = 90

    def wrap(self, aW, aH):
        self._w = aW
        return aW, self._h

    def draw(self):
        c = self.canv
        w, h = self._w, self._h

        # Card background
        c.setFillColor(C_PRIMARY)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=0)

        # Score circle
        cx, cy, r = 52, h / 2, 34
        c.setFillColor(HexColor('#1a2d5a'))
        c.setStrokeColor(C_ACCENT)
        c.setLineWidth(2)
        c.circle(cx, cy, r, fill=1, stroke=1)
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 20)
        c.drawCentredString(cx, cy + 6, str(self._score))
        c.setFont('Helvetica', 7)
        c.setFillColor(HexColor('#94A3B8'))
        c.drawCentredString(cx, cy - 8, f'/ {self._max}')

        # Grade pill
        tx = 100
        c.setFillColor(HexColor('#1a3a6b'))
        c.roundRect(tx, h - 24, 105, 16, 8, fill=1, stroke=0)
        c.setFillColor(C_ACCENT)
        c.setFont('Helvetica-Bold', 7)
        c.drawString(tx + 8, h - 19, self._grade)

        # Title
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 14)
        c.drawString(tx, h - 44, self._title)

        # Description lines
        c.setFillColor(HexColor('#94A3B8'))
        c.setFont('Helvetica', 8)
        for i, line in enumerate(self._desc.split('\n')):
            c.drawString(tx, h - 58 - (i * 12), line)
```

### SectionHeader

```python
class SectionHeader(Flowable):
    """Icon box + title text + subtitle + bottom border rule."""
    def __init__(self, icon: str, title: str, subtitle: str):
        super().__init__()
        self._icon  = icon
        self._title = title
        self._sub   = subtitle
        self._h     = 46

    def wrap(self, aW, aH):
        self._w = aW
        return aW, self._h

    def draw(self):
        c = self.canv
        # Icon box
        c.setFillColor(C_LIGHT)
        c.roundRect(0, 10, 30, 28, 5, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 13)
        c.setFillColor(C_TEXT)
        c.drawCentredString(15, 20, self._icon)
        # Title
        c.setFont('Helvetica-Bold', 14)
        c.setFillColor(C_PRIMARY)
        c.drawString(40, 26, self._title)
        # Subtitle
        c.setFont('Helvetica', 8)
        c.setFillColor(C_MUTED)
        c.drawString(40, 13, self._sub)
        # Bottom rule
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.line(0, 4, self._w, 4)
```

> **Icon note:** ReportLab's standard fonts don't render emoji. Use simple ASCII symbols or
> single characters: `'O'` for score, `'*'` for breakdown, `'+'` for citations, `'='` for verdict.
> If emoji support is needed, embed a Unicode font (see Font section below).

### VerdictCard

```python
from reportlab.lib.utils import simpleSplit

class VerdictCard(Flowable):
    """Dark header bar + body text + recommendation pill."""
    def __init__(self, verdict_text: str, recommendation: str, height: int = 130):
        super().__init__()
        self._text = verdict_text
        self._rec  = recommendation
        self._h    = height

    def wrap(self, aW, aH):
        self._w = aW
        return aW, self._h

    def draw(self):
        c = self.canv
        w, h = self._w, self._h

        # Outer border
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 8, fill=0, stroke=1)

        # Dark header bar (roundRect + rect overlap to square bottom corners)
        c.setFillColor(C_PRIMARY)
        c.roundRect(0, h - 38, w, 38, 8, fill=1, stroke=0)
        c.rect(0, h - 46, w, 12, fill=1, stroke=0)

        # Header text
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(16, h - 24, 'Editorial Assessment')

        # Body text (auto-wrapped)
        c.setFillColor(C_TEXT)
        c.setFont('Helvetica', 9)
        lines = simpleSplit(self._text, 'Helvetica', 9, w - 32)
        y = h - 60
        for line in lines:
            c.drawString(16, y, line)
            y -= 13

        # Recommendation label
        c.setFont('Helvetica', 7)
        c.setFillColor(C_MUTED)
        c.drawString(16, y - 4, 'RECOMMENDATION')

        # Rec pill
        pill_y = y - 26
        c.setFillColor(HexColor('#FFFBEB'))
        c.setStrokeColor(HexColor('#F59E0B'))
        c.setLineWidth(1.5)
        c.roundRect(16, pill_y, 200, 20, 5, fill=1, stroke=1)
        c.setFillColor(HexColor('#92400E'))
        c.setFont('Helvetica-Bold', 9)
        c.drawString(28, pill_y + 6, f'!  {self._rec}')
```

---

## Parameter Card Grid

Parameters are laid out as a **2-column grid** using a nested Table structure.

```python
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_RIGHT

AVAIL_W = W - 2 * MARGIN_H
COL_W   = (AVAIL_W - 5 * mm) / 2

def make_param_cell(name: str, score: int, total: int, issues: list, suggestions: list) -> list:
    """Returns a list of flowables for one parameter cell."""
    pct = score / total

    # Score bar color by percentage
    if pct >= 0.80:   bar_color = C_SUCCESS
    elif pct >= 0.60: bar_color = C_WARNING
    else:             bar_color = C_DANGER

    content = [
        # Name + score on one row
        Table([[
            Paragraph(f'<b>{name}</b>', S('pn', fontSize=9, textColor=C_PRIMARY)),
            Paragraph(
                f'<b>{score}</b><font size=8 color="#64748B"> / {total}</font>',
                S('ps', fontSize=11, textColor=C_PRIMARY, alignment=TA_RIGHT)
            ),
        ]], colWidths=[COL_W * 0.62, COL_W * 0.38],
        style=TableStyle([
            ('VALIGN',         (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING',     (0,0), (-1,-1), 0),
            ('BOTTOMPADDING',  (0,0), (-1,-1), 4),
            ('LEFTPADDING',    (0,0), (-1,-1), 0),
            ('RIGHTPADDING',   (0,0), (-1,-1), 0),
        ])),

        # Progress bar
        ProgressBar(pct, color=bar_color),
        Spacer(1, 3),
    ]

    # Issues list
    for issue in issues:
        content.append(Paragraph(
            f'<font color="#EF4444" size=7><b>ISSUE</b></font>  '
            f'<font size=8 color="#64748B">{issue}</font>',
            S('issue', leading=11)
        ))

    # Suggestions list
    for suggestion in suggestions:
        content.append(Paragraph(
            f'<font color="#10B981" size=7><b>FIX</b></font>  '
            f'<font size=8 color="#64748B">{suggestion}</font>',
            S('fix', leading=11)
        ))

    return content


def make_param_row(left_param: dict, right_param: dict | None) -> Table:
    """Wraps two param cells in a 2-column row table."""
    def wrap_cell(p):
        content = make_param_cell(
            p['name'], p['score'], p['total'],
            p.get('issues', []), p.get('suggestions', [])
        )
        pct = p['score'] / p['total']
        border_color = C_SUCCESS if pct >= 0.80 else (C_WARNING if pct >= 0.60 else C_DANGER)

        return Table([[content]], colWidths=[COL_W],
            style=TableStyle([
                ('LINEABOVE',     (0,0), (0,0),  3,   border_color),
                ('BOX',           (0,0), (-1,-1), 0.5, C_BORDER),
                ('BACKGROUND',    (0,0), (-1,-1), white),
                ('TOPPADDING',    (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING',   (0,0), (-1,-1), 8),
                ('RIGHTPADDING',  (0,0), (-1,-1), 8),
                ('VALIGN',        (0,0), (-1,-1), 'TOP'),
            ]))

    left_cell  = wrap_cell(left_param)
    right_cell = wrap_cell(right_param) if right_param else Spacer(COL_W, 1)

    return Table([[left_cell, right_cell]], colWidths=[COL_W, COL_W],
        style=TableStyle([
            ('LEFTPADDING',   (0,0), (-1,-1), 0),
            ('RIGHTPADDING',  (0,0), (-1,-1), 0),
            ('TOPPADDING',    (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
            ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ]))


def build_param_grid(parameters: list) -> list:
    """Returns a list of flowables for the full parameter grid."""
    flowables = []
    for i in range(0, len(parameters), 2):
        left  = parameters[i]
        right = parameters[i + 1] if i + 1 < len(parameters) else None
        flowables.append(make_param_row(left, right))
        flowables.append(Spacer(1, 3))
    return flowables
```

---

## Citation Analysis Section

```python
def build_citation_section(citation_data: dict) -> list:
    """
    citation_data = {
        'total': 5, 'verified': 3, 'unverified': 2,
        'flagged_dois': ['10.9999/fake-doi-1', '10.9999/fake-doi-2']
    }
    """
    flowables = []
    total      = citation_data['total']
    verified   = citation_data['verified']
    unverified = citation_data['unverified']
    success_pct = int((verified / total * 100) if total else 0)

    # Stats row (4 equal columns)
    q = AVAIL_W / 4

    def stat_cell(value, label, color):
        return Table([
            [Paragraph(f'<b>{value}</b>', S('sv', fontSize=20, textColor=color,
                                             alignment=TA_CENTER, leading=22))],
            [Paragraph(label, S('sl', fontSize=7, textColor=C_MUTED, alignment=TA_CENTER))],
        ], style=TableStyle([
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))

    stats_table = Table([[
        stat_cell(total,          'TOTAL DOIs',   C_PRIMARY),
        stat_cell(verified,       'VERIFIED',     C_SUCCESS),
        stat_cell(unverified,     'UNVERIFIED',   C_DANGER),
        stat_cell(f'{success_pct}%', 'SUCCESS RATE', C_PRIMARY),
    ]], colWidths=[q, q, q, q],
    style=TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), C_LIGHT),
        ('BOX',           (0,0), (-1,-1), 0.5, HexColor('#C7D8FF')),
        ('TOPPADDING',    (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    flowables.append(stats_table)
    flowables.append(Spacer(1, 3 * mm))

    # Flagged DOI rows
    if citation_data.get('flagged_dois'):
        doi_rows = []
        for doi in citation_data['flagged_dois']:
            doi_rows.append([
                Paragraph('<font color="#EF4444">●</font>', S('d', fontSize=9)),
                Paragraph(f'<font face="Courier" size=9>{doi}</font>', S('dc')),
                Paragraph('<b><font color="#EF4444" size=8>Not Found in CrossRef</font></b>',
                           S('ds', alignment=TA_RIGHT)),
            ])

        doi_table = Table(doi_rows,
            colWidths=[8 * mm, AVAIL_W - 55 * mm, 47 * mm],
            style=TableStyle([
                ('BACKGROUND',    (0,0), (-1,-1), C_LIGHT),
                ('LINEBELOW',     (0,0), (-1,-2), 0.5, HexColor('#DDE8FF')),
                ('BOX',           (0,0), (-1,-1), 0.5, HexColor('#C7D8FF')),
                ('LEFTPADDING',   (0,0), (-1,-1), 10),
                ('RIGHTPADDING',  (0,0), (-1,-1), 10),
                ('TOPPADDING',    (0,0), (-1,-1), 7),
                ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ]))
        flowables.append(doi_table)

    return flowables
```

---

## Full Story Builder

```python
from reportlab.platypus import PageBreak, Spacer

def build_story(report_data: dict) -> list:
    story = []

    # ── PAGE 2: Overall Score + Parameter Breakdown ──────────────────────
    story.append(SectionHeader('O', 'Overall Score',
        'Composite score across all weighted evaluation parameters'))
    story.append(Spacer(1, 4 * mm))
    story.append(ScoreHero(
        score       = report_data['score'],
        max_score   = report_data['max_score'],
        grade_label = f"Grade {report_data['grade']} · {report_data['grade_label']}",
        title       = report_data['grade_label'],
        description = report_data.get('score_description', ''),
    ))
    story.append(Spacer(1, 7 * mm))

    story.append(SectionHeader('*', 'Parameter Breakdown',
        'Each parameter is weighted differently — total adds up to 100 marks'))
    story.append(Spacer(1, 4 * mm))
    story.extend(build_param_grid(report_data['parameters']))

    # ── PAGE 3: Citation Analysis + Verdict ──────────────────────────────
    story.append(PageBreak())

    story.append(SectionHeader('+', 'Citation Analysis',
        'DOI verification via CrossRef database'))
    story.append(Spacer(1, 4 * mm))
    story.extend(build_citation_section(report_data['citations']))
    story.append(Spacer(1, 7 * mm))

    story.append(SectionHeader('=', 'Verdict',
        'Final assessment and editorial recommendation'))
    story.append(Spacer(1, 4 * mm))
    story.append(VerdictCard(
        verdict_text   = report_data['verdict_text'],
        recommendation = report_data['recommendation'],
    ))

    return story
```

---

## report_data Schema

`report_generator.py` expects this dict structure:

```python
report_data = {
    # Cover + score
    'paper_name':        'my_paper.pdf',
    'analysed_at':       '19 May 2026 — 17:05',
    'score':             70,
    'max_score':         100,
    'grade':             'B',
    'grade_label':       'Good',
    'score_description': 'Solid foundational work.\nTargeted revisions will strengthen the submission.',
    'status':            'Minor Revision Required',

    # Parameters (list of dicts, any length)
    'parameters': [
        {
            'name':        'Grammar & Language',
            'score':       10,
            'total':       15,
            'issues':      ['Passive voice overuse', 'Inconsistent tense'],
            'suggestions': ['Revise passive constructions', 'Standardise to past tense'],
        },
        # ... more parameters
    ],

    # Citations
    'citations': {
        'total':       5,
        'verified':    3,
        'unverified':  2,
        'flagged_dois': ['10.9999/fake-doi-1', '10.9999/fake-doi-2'],
    },

    # Verdict
    'verdict_text':    'This paper shows good overall quality...',
    'recommendation':  'Minor Revision Required',
}
```

---

## Font Support (Optional Emoji Icons)

ReportLab's built-in Helvetica/Courier don't render emoji. Two options:

**Option A — ASCII symbols (default, zero setup):**
```python
ICONS = {'score': 'O', 'params': '*', 'citations': '+', 'verdict': '='}
```

**Option B — Register a Unicode font (full emoji support):**
```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Requires: pip install reportlab[fonts] or a system font path
pdfmetrics.registerFont(TTFont('NotoSans', '/path/to/NotoSans-Regular.ttf'))
# Then use fontName='NotoSans' in ParagraphStyle or canvas.setFont()
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `LayoutError: Flowable too large` | Flowable height exceeds frame | Reduce `self._h`, or split into smaller flowables |
| `AttributeError: 'NoneType' on canv` | `draw()` called before `wrap()` | Always call `wrap()` first (PLATYPUS does this automatically) |
| Missing `super().__init__()` | Flowable internal state broken | Always call `super().__init__()` in `__init__` |
| Blank/truncated text in VerdictCard | `simpleSplit` width too narrow | Increase `w - 32` or reduce font size |
| Cover page content missing | `onPage` callback not bound | Ensure `PageTemplate(onPage=draw_cover)` is set |
| Two-column grid misaligned | `colWidths` sum > frame width | Recalculate: `COL_W = (AVAIL_W - gap) / 2` |
| `report_data` not available in callback | Not attached to doc | Add `doc.report_data = report_data` before `doc.build()` |
| Progress bar overflows cell | Width not captured in `wrap()` | Confirm `self._w = aW` inside `wrap()` |

---

## Checklist Before Running

- [ ] `report_data` dict has all required keys
- [ ] `doc.report_data = report_data` set before `doc.build()`
- [ ] `NextPageTemplate('content')` + `PageBreak()` prepended to story
- [ ] `COL_W * 2 <= AVAIL_W` (no column overflow)
- [ ] `VerdictCard` height large enough for `verdict_text` length
- [ ] Output written to `/mnt/user-data/outputs/` for download
