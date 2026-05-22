"""
report_generator.py — ResearchSense PDF Report Generator

Architecture: PLATYPUS Hybrid (BaseDocTemplate + custom Flowables + Canvas callbacks)
Skill ref:   antigravity-reportlab-pdf.skill

Cover page:  Full-bleed dark navy Canvas callback (onPage)
Content:     PLATYPUS story list with auto page breaks
Components:  ProgressBar, ScoreHero, SectionHeader, VerdictCard (custom Flowables)
"""

import io
import os
from datetime import datetime

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, NextPageTemplate, PageBreak,
    Flowable, Paragraph, Spacer, Table, TableStyle,
)

# Use the failover-capable LLM client from gemini_analyzer
from gemini_analyzer import _call_llm_with_failover


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Color Tokens — single source of truth (never hardcode hex in components)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

C_PRIMARY = HexColor('#0F1B35')   # dark navy — backgrounds, headings
C_ACCENT  = HexColor('#4F8EF7')   # blue — borders, highlights, pills
C_ACCENT2 = HexColor('#7C3AED')   # purple — gradient bar, decorative
C_WARNING = HexColor('#F59E0B')   # amber — medium score bars & borders
C_SUCCESS = HexColor('#10B981')   # green — verified DOIs, fix labels
C_DANGER  = HexColor('#EF4444')   # red — issues, unverified DOIs
C_LIGHT   = HexColor('#F0F4FF')   # light blue-grey — card backgrounds
C_TEXT    = HexColor('#1E293B')   # near-black — body text
C_MUTED   = HexColor('#64748B')   # grey — subtitles, labels
C_BORDER  = HexColor('#E2E8F0')   # light grey — dividers, box borders


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

W, H = A4
MARGIN_H = 18 * mm   # left/right
MARGIN_T = 14 * mm   # top
MARGIN_B = 16 * mm   # bottom (space for footer)
AVAIL_W  = W - 2 * MARGIN_H
COL_W    = (AVAIL_W - 5 * mm) / 2

# Max marks per parameter (must match scoring.py WEIGHTS * 100)
MAX_MARKS = {
    "structure_sections": 20,
    "clarity_writing":    25,
    "methodology_rigor":  25,
    "evidence_claims":    20,
    "citations":          10,
}

PARAM_LABELS = {
    "structure_sections": "Structure & Sections",
    "clarity_writing":    "Clarity & Writing",
    "methodology_rigor":  "Methodology Rigor",
    "evidence_claims":    "Evidence & Claims",
    "citations":          "Citations & References",
}

PARAM_ORDER = [
    "structure_sections", "clarity_writing", "methodology_rigor",
    "evidence_claims", "citations",
]

# Recommendation — exactly 4 fixed strings, no variation (R-01)
RECOMMENDATION_MAP = {
    "A": "Recommendation: Ready for Submission",
    "B": "Recommendation: Minor Revision Required",
    "C": "Recommendation: Major Revision Required",
    "D": "Recommendation: Not Suitable for Submission",
    "F": "Recommendation: Not Suitable for Submission",
}

GRADE_LABELS = {
    "A": "Excellent",
    "B": "Good",
    "C": "Needs Improvement",
    "D": "Poor",
    "F": "Very Poor",
}

GRADE_QUALITY_TITLES = {
    "A": "Excellent Overall Quality",
    "B": "Good Overall Quality",
    "C": "Fair Overall Quality",
    "D": "Poor Overall Quality",
    "F": "Very Poor Overall Quality",
}

SCORE_DESCRIPTIONS = {
    "A": "The paper demonstrates excellence across all evaluation dimensions.\n"
         "It is ready for submission with only minor cosmetic adjustments.",
    "B": "The paper demonstrates solid foundational work across most dimensions.\n"
         "Targeted revisions will meaningfully strengthen the submission.",
    "C": "The paper has significant areas requiring improvement.\n"
         "A thorough revision addressing flagged issues is recommended.",
    "D": "The paper requires substantial work across multiple dimensions.\n"
         "Major revision is needed before resubmission.",
    "F": "The paper does not meet minimum standards for academic submission.\n"
         "A fundamental rework of the manuscript is recommended.",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Style Helper
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_style_counter = 0

def S(name, **kw):
    """Create a ParagraphStyle with sensible defaults and unique name."""
    global _style_counter
    _style_counter += 1
    defaults = dict(
        fontName='Helvetica', fontSize=10,
        textColor=C_TEXT, leading=14,
        spaceAfter=0, spaceBefore=0,
    )
    defaults.update(kw)
    return ParagraphStyle(f"{name}_{_style_counter}", **defaults)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Gemini Verdict (Hybrid R-01)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_grade_letter(grade: str) -> str:
    """Extract letter from grade string e.g. 'B — Good' → 'B'."""
    return grade.strip()[0].upper() if grade.strip() else "F"


def _generate_verdict_paragraph(
    final_score: float,
    grade: str,
    layer_scores: dict,
    layer_details: dict,
) -> str:
    """
    LLM writes a 2–3 sentence summary paragraph using the failover client.
    Falls back to template if all providers are unavailable.
    """
    sorted_layers = sorted(layer_scores.items(), key=lambda x: x[1])
    worst_two = sorted_layers[:2]
    top_issues = []
    for layer_key, _ in worst_two:
        details = layer_details.get(layer_key, {})
        issues = details.get("issues", [])
        if issues:
            top_issues.append(
                f"{PARAM_LABELS.get(layer_key, layer_key)}: {issues[0]}"
            )

    prompt = (
        "You are writing a short verdict for an academic paper analysis report.\n"
        "Based on the scores below, write exactly 2-3 sentences summarising the paper's "
        "overall quality. Be specific, professional, and concise.\n"
        "Do not repeat the grade or recommendation \u2014 those are shown separately.\n"
        "Do not use bullet points. Plain prose only.\n\n"
        f"Final score: {final_score}/100 ({grade})\n"
        "Key issues found:\n" + "\n".join(f"- {i}" for i in top_issues)
    )

    try:
        return _call_llm_with_failover(prompt)
    except Exception:
        grade_letter = _get_grade_letter(grade)
        fallbacks = {
            "A": f"This paper demonstrates strong quality across all evaluated dimensions, "
                 f"achieving a final score of {final_score}/100. "
                 "It meets the standards expected for academic submission.",
            "B": f"This paper shows good overall quality with a score of {final_score}/100, "
                 "but has areas that would benefit from revision. "
                 "Addressing the identified issues will strengthen the submission.",
            "C": f"This paper requires significant revision before it is ready for submission, "
                 f"scoring {final_score}/100. "
                 "The issues identified across multiple dimensions need to be addressed thoroughly.",
        }
        return fallbacks.get(
            grade_letter,
            f"This paper is not suitable for submission in its current state, "
            f"scoring {final_score}/100. "
            "Substantial revisions are required across multiple evaluation dimensions."
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Canvas Callbacks (Cover + Footer)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def draw_cover(canvas, doc):
    """Full-bleed dark cover page — 100% Canvas, no PLATYPUS flowables."""
    canvas.saveState()
    rd = doc.report_data

    # 1. Dark background
    canvas.setFillColor(C_PRIMARY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # 2. Decorative circles (subtle, low alpha)
    for (x, y, r, col, a) in [
        (W + 50, H + 50, 170, C_ACCENT,  0.07),
        (-50,    100,    120, C_ACCENT2, 0.06),
        (W - 50, 220,    70,  C_ACCENT,  0.05),
    ]:
        canvas.setFillAlpha(a)
        canvas.setFillColor(col)
        canvas.circle(x, y, r, fill=1, stroke=0)
    canvas.setFillAlpha(1)

    # 3. Top gradient bar (blue → purple)
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, H - 4, W * 0.55, 4, fill=1, stroke=0)
    canvas.setFillColor(C_ACCENT2)
    canvas.rect(W * 0.45, H - 4, W * 0.55, 4, fill=1, stroke=0)

    # 4. Brand name
    canvas.setFillColor(C_ACCENT)
    canvas.circle(36, H - 52, 5, fill=1, stroke=0)
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

    # 8. Metadata grid (2 cols × 2 rows)
    canvas.setStrokeColor(HexColor('#1e3a6e'))
    canvas.setLineWidth(0.5)
    canvas.line(36, H - 238, W - 36, H - 238)

    meta = [
        ('PAPER',              rd.get('paper_name', 'paper.pdf')),
        ('ANALYSED',           rd.get('analysed_at', '')),
        ('PARAMETERS EVALUATED', f"{len(rd.get('parameters', []))} Dimensions"),
        ('STATUS',             rd.get('status', '')),
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

    # 9. Score badge (bottom-right circle)
    bx, by = W - 72, 72
    canvas.setFillColor(HexColor('#1a2d5a'))
    canvas.setStrokeColor(C_ACCENT)
    canvas.setLineWidth(2)
    canvas.circle(bx, by, 52, fill=1, stroke=1)
    canvas.setFillColor(white)
    canvas.setFont('Helvetica-Bold', 24)
    canvas.drawCentredString(bx, by + 8, str(rd['score']))
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(HexColor('#94A3B8'))
    canvas.drawCentredString(bx, by - 6, f"/ {rd['max_score']}")
    canvas.setFillColor(C_ACCENT)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(bx, by - 22, f"Grade {rd['grade']}")

    canvas.restoreState()


def draw_footer(canvas, doc):
    """Footer on every content page (skip cover)."""
    if doc.page > 1:
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(HexColor('#94A3B8'))
        canvas.drawCentredString(
            W / 2, 10 * mm,
            f"ResearchSense  ·  Analysis Report  ·  Page {doc.page}"
        )
        canvas.restoreState()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Custom Flowables
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ProgressBar(Flowable):
    """Thin horizontal bar showing score percentage."""
    def __init__(self, pct, color=C_WARNING, height=5):
        super().__init__()
        self._pct = min(max(pct, 0), 1)
        self._color = color
        self._h = height + 4

    def wrap(self, aW, aH):
        self._w = aW
        return aW, self._h

    def draw(self):
        c = self.canv
        bar_h = self._h - 4
        # Track
        c.setFillColor(C_BORDER)
        c.roundRect(0, 2, self._w, bar_h, 2, fill=1, stroke=0)
        # Fill
        c.setFillColor(self._color)
        c.roundRect(0, 2, max(4, self._w * self._pct), bar_h, 2, fill=1, stroke=0)


class ScoreHero(Flowable):
    """Dark navy card: circular score + grade pill + label + description."""
    def __init__(self, score, max_score, grade_label, title, description):
        super().__init__()
        self._score = score
        self._max   = max_score
        self._grade = grade_label
        self._title = title
        self._desc  = description
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
        c.roundRect(tx, h - 24, 130, 16, 8, fill=1, stroke=0)
        c.setFillColor(C_ACCENT)
        c.setFont('Helvetica-Bold', 7)
        c.drawString(tx + 8, h - 19, self._grade.upper())

        # Title
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 14)
        c.drawString(tx, h - 44, self._title)

        # Description lines
        c.setFillColor(HexColor('#94A3B8'))
        c.setFont('Helvetica', 8)
        for i, line in enumerate(self._desc.split('\n')):
            c.drawString(tx, h - 58 - (i * 12), line)


class SectionHeader(Flowable):
    """Icon box + title text + subtitle + bottom border rule."""
    def __init__(self, icon, title, subtitle):
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


class VerdictCard(Flowable):
    """Dark header bar + body text + recommendation pill."""
    def __init__(self, verdict_text, recommendation, height=140):
        super().__init__()
        self._text = verdict_text
        self._rec  = recommendation
        self._h    = height

    def wrap(self, aW, aH):
        self._w = aW
        # Dynamically calculate height based on text length
        lines = simpleSplit(self._text, 'Helvetica', 9, self._w - 32)
        text_height = len(lines) * 13
        self._h = max(self._h, text_height + 90)  # header + padding + rec pill
        return aW, self._h

    def draw(self):
        c = self.canv
        w, h = self._w, self._h

        # Outer border
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 8, fill=0, stroke=1)

        # Dark header bar
        c.setFillColor(C_PRIMARY)
        c.roundRect(0, h - 38, w, 38, 8, fill=1, stroke=0)
        c.rect(0, h - 46, w, 12, fill=1, stroke=0)  # square bottom corners

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

        # Recommendation pill
        pill_y = y - 26
        c.setFillColor(HexColor('#FFFBEB'))
        c.setStrokeColor(HexColor('#F59E0B'))
        c.setLineWidth(1.5)
        c.roundRect(16, pill_y, w - 32, 20, 5, fill=1, stroke=1)
        c.setFillColor(HexColor('#92400E'))
        c.setFont('Helvetica-Bold', 9)
        c.drawString(28, pill_y + 6, f'!  {self._rec}')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Parameter Card Grid (2-column layout)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _bar_color(pct):
    """Pick progress bar colour based on score percentage."""
    if pct >= 0.80:
        return C_SUCCESS
    elif pct >= 0.60:
        return C_WARNING
    else:
        return C_DANGER


def _make_param_cell(name, score, total, issues, suggestions):
    """Build flowable content for one parameter cell."""
    pct = score / total if total else 0
    color = _bar_color(pct)

    content = [
        # Name + score row
        Table([[
            Paragraph(f'<b>{name}</b>',
                      S('pn', fontSize=9, textColor=C_PRIMARY)),
            Paragraph(
                f'<b>{score}</b><font size=8 color="#64748B"> / {total}</font>',
                S('ps', fontSize=11, textColor=C_PRIMARY, alignment=TA_RIGHT)),
        ]], colWidths=[COL_W * 0.55, COL_W * 0.45 - 16],
        style=TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ])),

        # Progress bar
        ProgressBar(pct, color=color),
        Spacer(1, 3),
    ]

    # Issues
    for issue in issues:
        content.append(Paragraph(
            f'<font color="#EF4444" size=7><b>ISSUE:</b></font>  '
            f'<font size=8 color="#64748B">{issue}</font>',
            S('issue', leading=11),
        ))

    # Suggestions
    for sug in suggestions:
        content.append(Paragraph(
            f'<font color="#10B981" size=7><b>FIX:</b></font>  '
            f'<font size=8 color="#64748B">{sug}</font>',
            S('fix', leading=11),
        ))

    return content


def _make_param_row(left, right=None):
    """Wrap two parameter cells in a 2-column table row."""
    def _wrap_cell(p):
        content = _make_param_cell(
            p['name'], p['score'], p['total'],
            p.get('issues', []), p.get('suggestions', []),
        )
        pct = p['score'] / p['total'] if p['total'] else 0
        border_color = _bar_color(pct)

        return Table([[content]], colWidths=[COL_W],
            style=TableStyle([
                ('LINEABOVE',     (0, 0), (0, 0),   3,   border_color),
                ('BOX',           (0, 0), (-1, -1), 0.5, C_BORDER),
                ('BACKGROUND',    (0, 0), (-1, -1), white),
                ('TOPPADDING',    (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
                ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ]))

    left_cell  = _wrap_cell(left)
    right_cell = _wrap_cell(right) if right else Spacer(COL_W, 1)

    return Table([[left_cell, right_cell]], colWidths=[COL_W, COL_W],
        style=TableStyle([
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
        ]))


def _build_param_grid(parameters):
    """Build the full 2-column parameter grid flowables."""
    flowables = []
    for i in range(0, len(parameters), 2):
        left = parameters[i]
        right = parameters[i + 1] if i + 1 < len(parameters) else None
        flowables.append(_make_param_row(left, right))
        flowables.append(Spacer(1, 3))
    return flowables


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Citation Analysis Section
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_citation_section(citation_data):
    """Build citation stats row + flagged items table."""
    flowables = []
    total_refs = citation_data.get('total_refs', 0)
    verified   = citation_data.get('verified', 0)
    unverified = citation_data.get('unverified', 0)
    success_pct = int((verified / total_refs * 100) if total_refs else 0)

    if total_refs == 0:
        flowables.append(Paragraph(
            "No references detected in the paper.",
            S('body', fontSize=10, textColor=C_MUTED),
        ))
        return flowables

    # Stats row (4 equal columns)
    q = AVAIL_W / 4

    def _stat_cell(value, label, color):
        return Table([
            [Paragraph(f'<b>{value}</b>',
                       S('sv', fontSize=20, textColor=color,
                         alignment=TA_CENTER, leading=22))],
            [Paragraph(label,
                       S('sl', fontSize=7, textColor=C_MUTED,
                         alignment=TA_CENTER))],
        ], style=TableStyle([
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING',    (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

    stats_table = Table([[
        _stat_cell(verified,          'VERIFIED',      C_SUCCESS),
        _stat_cell(total_refs,        'TOTAL REFS',    C_PRIMARY),
        _stat_cell(unverified,        'UNVERIFIED',    C_DANGER),
        _stat_cell(f'{success_pct}%', 'SUCCESS RATE',  C_PRIMARY),
    ]], colWidths=[q, q, q, q],
    style=TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), C_LIGHT),
        ('BOX',           (0, 0), (-1, -1), 0.5, HexColor('#C7D8FF')),
        ('TOPPADDING',    (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    flowables.append(stats_table)
    flowables.append(Spacer(1, 3 * mm))

    # Flagged items with categories
    flagged_items = citation_data.get('flagged_items', [])
    if flagged_items:
        flag_rows = []
        CATEGORY_COLORS = {
            'duplicate': HexColor('#F59E0B'),   # amber
            'not_found': HexColor('#EF4444'),   # red
            'missing':   HexColor('#8B5CF6'),   # purple
        }
        CATEGORY_LABELS = {
            'duplicate': 'Duplicate',
            'not_found': 'Not found',
            'missing':   'Missing',
        }
        for item in flagged_items:
            cat = item.get('category', 'not_found')
            color = CATEGORY_COLORS.get(cat, C_DANGER)
            label = CATEGORY_LABELS.get(cat, cat.title())
            flag_rows.append([
                Paragraph(f'<font color="{color.hexval()}">\u26a0</font>',
                          S('d', fontSize=9)),
                Paragraph(
                    f'<b>{item.get("citation", "Unknown")}</b>',
                    S('dc', fontSize=9)),
                Paragraph(
                    f'<b><font color="{color.hexval()}" size=7>{label}</font></b>'
                    f' <font size=7 color="#64748B">\u00b7 {item.get("detail", "")}</font>',
                    S('ds', fontSize=8)),
            ])

        flag_table = Table(flag_rows,
            colWidths=[8 * mm, 45 * mm, AVAIL_W - 53 * mm],
            style=TableStyle([
                ('BACKGROUND',    (0, 0), (-1, -1), C_LIGHT),
                ('LINEBELOW',     (0, 0), (-1, -2), 0.5, HexColor('#DDE8FF')),
                ('BOX',           (0, 0), (-1, -1), 0.5, HexColor('#C7D8FF')),
                ('LEFTPADDING',   (0, 0), (-1, -1), 10),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
                ('TOPPADDING',    (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ]))
        flowables.append(flag_table)

    return flowables


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Story Builder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_detected_sections(detected_sections):
    """Build a pill grid showing detected sections with confidence %."""
    flowables = []
    if not detected_sections:
        flowables.append(Paragraph(
            "No sections detected.",
            S('body', fontSize=10, textColor=C_MUTED),
        ))
        return flowables

    # Build pill-like entries in a table (3 columns)
    pills = []
    for name, confidence in detected_sections.items():
        color = C_SUCCESS if confidence >= 85 else C_WARNING if confidence >= 70 else C_DANGER
        pills.append(Paragraph(
            f'<font color="{color.hexval()}">\u2713</font> '
            f'<b>{name}</b> <font size=8 color="#64748B">{confidence}%</font>',
            S('pill', fontSize=9, textColor=C_TEXT),
        ))

    # Layout in rows of 3
    pill_rows = []
    for i in range(0, len(pills), 3):
        row = pills[i:i+3]
        while len(row) < 3:
            row.append(Paragraph('', S('empty')))
        pill_rows.append(row)

    col_w = AVAIL_W / 3
    pill_table = Table(pill_rows, colWidths=[col_w, col_w, col_w],
        style=TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), C_LIGHT),
            ('BOX',           (0, 0), (-1, -1), 0.5, HexColor('#C7D8FF')),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ]))
    flowables.append(pill_table)
    return flowables


def _build_story(report_data):
    """Build the full PLATYPUS story (cover is handled by onPage callback)."""
    story = []

    # ── Overall Score
    story.append(SectionHeader('O', 'Overall Score',
        'Composite score across all weighted evaluation parameters'))
    story.append(Spacer(1, 4 * mm))
    story.append(ScoreHero(
        score       = report_data['score'],
        max_score   = report_data['max_score'],
        grade_label = f"Grade {report_data['grade']} - {report_data['grade_label']}",
        title       = report_data.get('quality_title', 'Overall Quality'),
        description = report_data.get('score_description', ''),
    ))
    story.append(Spacer(1, 7 * mm))

    # ── Detected Sections
    story.append(SectionHeader('S', 'Detected Sections',
        'Sections identified in the paper with confidence scores'))
    story.append(Spacer(1, 4 * mm))
    story.extend(_build_detected_sections(report_data.get('detected_sections', {})))
    story.append(Spacer(1, 7 * mm))

    # ── Multi-Layer Analysis
    story.append(SectionHeader('*', 'Multi-Layer Analysis',
        '5 weighted dimensions \u2014 total adds up to 100 marks'))
    story.append(Spacer(1, 4 * mm))
    story.extend(_build_param_grid(report_data['parameters']))

    # ── Citation Check + Verdict (new page)
    story.append(PageBreak())

    story.append(SectionHeader('+', 'Citation Check',
        'Reference verification via CrossRef database'))
    story.append(Spacer(1, 4 * mm))
    story.extend(_build_citation_section(report_data['citations']))
    story.append(Spacer(1, 7 * mm))

    story.append(SectionHeader('=', 'Verdict',
        'Final assessment and editorial recommendation'))
    story.append(Spacer(1, 4 * mm))
    story.append(VerdictCard(
        verdict_text   = report_data['verdict_text'],
        recommendation = report_data['recommendation'],
    ))

    return story


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Public API (called by main.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_pdf_report(
    filename: str,
    layer_scores: dict,
    layer_details: dict,
    final_score: float,
    grade: str,
    citation_result: dict,
    detected_sections: dict = None,
) -> io.BytesIO:
    """
    Build the full themed PDF report and return as in-memory BytesIO buffer.

    Transforms the raw /analyze JSON into the report_data schema required
    by the skill architecture, then builds cover + content pages.
    """
    grade_letter = _get_grade_letter(grade)
    grade_label = GRADE_LABELS.get(grade_letter, "Unknown")
    quality_title = GRADE_QUALITY_TITLES.get(grade_letter, "Overall Quality")
    score_desc = SCORE_DESCRIPTIONS.get(grade_letter, "")
    recommendation = RECOMMENDATION_MAP.get(grade_letter, RECOMMENDATION_MAP["F"])
    status = recommendation.replace("Recommendation: ", "")

    # Generate LLM verdict paragraph
    verdict_text = _generate_verdict_paragraph(
        final_score, grade, layer_scores, layer_details,
    )

    # Build parameter list (converted from raw 0\u201310 scores to earned/max marks)
    parameters = []
    for key in PARAM_ORDER:
        max_m = MAX_MARKS[key]
        raw = layer_scores.get(key, 0.0)
        earned = round(raw * max_m / 10)
        details = layer_details.get(key, {})
        parameters.append({
            'name':        PARAM_LABELS.get(key, key.title()),
            'score':       earned,
            'total':       max_m,
            'issues':      details.get('issues', ['No issues recorded.']),
            'suggestions': details.get('suggestions', ['No suggestions recorded.']),
        })

    # Build report_data dict (skill schema)
    report_data = {
        'paper_name':        filename,
        'analysed_at':       datetime.now().strftime('%d %B %Y \u2014 %H:%M'),
        'score':             int(round(final_score)),
        'max_score':         100,
        'grade':             grade_letter,
        'grade_label':       grade_label,
        'quality_title':     quality_title,
        'score_description': score_desc,
        'status':            status,
        'parameters':        parameters,
        'detected_sections': detected_sections or {},
        'citations': {
            'total_refs':    citation_result.get('total_refs', 0),
            'verified':      citation_result.get('verified', 0),
            'unverified':    citation_result.get('not_found', 0)
                             + citation_result.get('unreachable', 0),
            'flagged_items': citation_result.get('flagged_items', []),
        },
        'verdict_text':     verdict_text,
        'recommendation':   status,
    }

    # ── Build PDF ─────────────────────────────────────────────────
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
        PageTemplate(id='cover',   frames=[Frame(0, 0, W, H, id='cf')],
                     onPage=draw_cover),
        PageTemplate(id='content', frames=[content_frame],
                     onPage=draw_footer),
    ])

    # Attach report_data for Canvas callbacks
    doc.report_data = report_data

    # Build: cover page (via NextPageTemplate switch) + content story
    story = [NextPageTemplate('content'), PageBreak()] + _build_story(report_data)
    doc.build(story)

    return buf
