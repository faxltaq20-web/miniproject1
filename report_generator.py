import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, ListFlowable, ListItem, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from google import genai
from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ─── Colour palette ───────────────────────────────────────────────
ACCENT = colors.HexColor("#1a73e8")
GRADE_COLORS = {
    "A": colors.HexColor("#34a853"),  # green
    "B": colors.HexColor("#1a73e8"),  # blue
    "C": colors.HexColor("#f9ab00"),  # amber
    "D": colors.HexColor("#ea4335"),  # red
    "F": colors.HexColor("#ea4335"),  # red
}

# ─── Max marks per parameter (must match scoring.py WEIGHTS) ──────
MAX_MARKS = {
    "grammar":     15,
    "structure":   15,
    "methodology": 15,
    "logic":       15,
    "readability": 10,
    "abstract":    10,
    "conclusion":  10,
    "citations":   10,
}

# ─── Display names ─────────────────────────────────────────────────
PARAM_LABELS = {
    "grammar":     "Grammar & Language",
    "structure":   "Structural Integrity",
    "methodology": "Methodology Soundness",
    "logic":       "Logical Consistency",
    "readability": "Readability Score",
    "abstract":    "Abstract Quality",
    "conclusion":  "Conclusion Completeness",
    "citations":   "Citation Quality",
}

# ─── Recommendation line — exactly 4 fixed strings (R-01) ─────────
RECOMMENDATION_MAP = {
    "A": "Recommendation: Ready for Submission",
    "B": "Recommendation: Minor Revision Required",
    "C": "Recommendation: Major Revision Required",
    "D": "Recommendation: Not Suitable for Submission",
    "F": "Recommendation: Not Suitable for Submission",
}

# ─── Section 3 parameter display order ────────────────────────────
PARAM_ORDER = [
    "grammar", "structure", "methodology", "logic",
    "readability", "abstract", "conclusion", "citations",
]


def _get_grade_letter(grade: str) -> str:
    """Extract first letter from grade string e.g. 'B — Good' → 'B'."""
    return grade.strip()[0].upper() if grade.strip() else "F"


def _generate_verdict_paragraph(
    final_score: float,
    grade: str,
    layer_scores: dict,
    layer_details: dict,
) -> str:
    """
    Call Gemini for the verdict summary paragraph (R-01 hybrid).
    Falls back to a template string if Gemini is unavailable.
    """
    # Pick the two worst layers to give Gemini specific context
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
        "Do not repeat the grade or recommendation — those are shown separately.\n"
        "Do not use bullet points. Plain prose only.\n\n"
        f"Final score: {final_score}/100 ({grade})\n"
        "Key issues found:\n" + "\n".join(f"- {i}" for i in top_issues)
    )

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()
    except Exception:
        # Fallback template — used when GEMINI_API_KEY is unavailable
        grade_letter = _get_grade_letter(grade)
        if grade_letter == "A":
            return (
                f"This paper demonstrates strong quality across all evaluated dimensions, "
                f"achieving a final score of {final_score}/100. "
                "It meets the standards expected for academic submission."
            )
        elif grade_letter == "B":
            return (
                f"This paper shows good overall quality with a score of {final_score}/100, "
                "but has areas that would benefit from revision. "
                "Addressing the identified issues will strengthen the submission."
            )
        elif grade_letter == "C":
            return (
                f"This paper requires significant revision before it is ready for submission, "
                f"scoring {final_score}/100. "
                "The issues identified across multiple dimensions need to be addressed thoroughly."
            )
        else:
            return (
                f"This paper is not suitable for submission in its current state, "
                f"scoring {final_score}/100. "
                "Substantial revisions are required across multiple evaluation dimensions."
            )


def _make_styles() -> dict:
    """Build paragraph styles for the report."""
    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=ACCENT,
            spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#5f6368"),
            spaceAfter=2,
            alignment=TA_CENTER,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=ACCENT,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "param_heading": ParagraphStyle(
            "ParamHeading",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=colors.HexColor("#202124"),
            spaceBefore=10,
            spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "Label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#5f6368"),
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#202124"),
            spaceAfter=4,
            leading=14,
        ),
        "verdict": ParagraphStyle(
            "Verdict",
            fontName="Helvetica",
            fontSize=11,
            textColor=colors.HexColor("#202124"),
            spaceAfter=8,
            leading=16,
        ),
        "recommendation": ParagraphStyle(
            "Recommendation",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=ACCENT,
            spaceAfter=4,
        ),
        "doi_flag": ParagraphStyle(
            "DoiFlag",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#ea4335"),
            spaceAfter=2,
        ),
    }
    return styles


def _footer(canvas, doc):
    """Render page footer on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#9aa0a6"))
    canvas.drawString(2 * cm, 1.2 * cm, "Generated by ResearchSense")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def generate_pdf_report(
    filename: str,
    layer_scores: dict,
    layer_details: dict,
    final_score: float,
    grade: str,
    citation_result: dict,
) -> io.BytesIO:
    """
    Build and return the full PDF report as an in-memory BytesIO buffer.

    Args:
        filename:        original uploaded PDF filename
        layer_scores:    {"grammar": float, ...} — 0-10 per layer
        layer_details:   {"grammar": {"score", "issues", "suggestions"}, ...}
        final_score:     0-100 weighted confidence score
        grade:           e.g. "B — Good"
        citation_result: {"total_dois", "verified", "not_found", "flagged_dois", ...}

    Returns:
        io.BytesIO buffer (caller must seek(0) before reading/streaming)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = _make_styles()
    story = []
    grade_letter = _get_grade_letter(grade)

    # ── SECTION 1: Header ─────────────────────────────────────────
    story.append(Paragraph("ResearchSense Analysis Report", styles["title"]))
    story.append(Paragraph(f"<b>Paper:</b> {filename}", styles["subtitle"]))
    story.append(Paragraph(
        f"<b>Analysed:</b> {datetime.now().strftime('%d %B %Y — %H:%M')}",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.3 * cm))

    # ── SECTION 2: Overall Score ───────────────────────────────────
    story.append(Paragraph("Overall Score", styles["section_heading"]))

    grade_color = GRADE_COLORS.get(grade_letter, colors.HexColor("#ea4335"))
    score_table = Table(
        [["Final Score", "Grade"], [f"{final_score} / 100", grade]],
        colWidths=[8 * cm, 8 * cm],
    )
    score_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 11),
        ("BACKGROUND",  (0, 1), (-1, 1), grade_color),
        ("TEXTCOLOR",   (0, 1), (-1, 1), colors.white),
        ("FONTNAME",    (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 1), (-1, 1), 14),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROWHEIGHT",   (0, 1), (-1, 1), 30),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.white),
        ("BOX",         (0, 0), (-1, -1), 1, ACCENT),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── SECTION 3: Parameter Breakdown ────────────────────────────
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#e0e0e0")
    ))
    story.append(Paragraph("Parameter Breakdown", styles["section_heading"]))
    story.append(Paragraph(
        "Each parameter is weighted differently — total adds up to 100 marks.",
        styles["body"],
    ))
    story.append(Spacer(1, 0.2 * cm))

    for key in PARAM_ORDER:
        max_m = MAX_MARKS[key]
        raw = layer_scores.get(key, 0.0)
        earned = round(raw * max_m / 10)  # R-05: marks conversion
        details = layer_details.get(key, {})
        issues = details.get("issues", ["No issues recorded."])
        suggestions = details.get("suggestions", ["No suggestions recorded."])
        label = PARAM_LABELS.get(key, key.title())

        heading = Paragraph(
            f"{label} &nbsp;&nbsp;&nbsp; "
            f"<font color='#1a73e8'><b>{earned} / {max_m}</b></font>",
            styles["param_heading"],
        )
        issues_label = Paragraph("Issues found:", styles["label"])
        issues_list = ListFlowable(
            [ListItem(Paragraph(i, styles["body"]), leftIndent=12) for i in issues],
            bulletType="bullet",
            leftIndent=18,
            spaceBefore=0,
        )
        suggestions_label = Paragraph("Suggestions:", styles["label"])
        suggestions_list = ListFlowable(
            [ListItem(Paragraph(s, styles["body"]), leftIndent=12) for s in suggestions],
            bulletType="bullet",
            leftIndent=18,
            spaceBefore=0,
        )

        story.append(KeepTogether([
            heading,
            issues_label,
            issues_list,
            suggestions_label,
            suggestions_list,
            Spacer(1, 0.15 * cm),
            HRFlowable(
                width="100%", thickness=0.5,
                color=colors.HexColor("#e0e0e0"),
            ),
        ]))

    # ── SECTION 4: Citations ───────────────────────────────────────
    story.append(Paragraph("Citation Analysis", styles["section_heading"]))

    total = citation_result.get("total_dois", 0)
    verified = citation_result.get("verified", 0)
    not_found = citation_result.get("not_found", 0)
    unreachable = citation_result.get("unreachable", 0)
    flagged = citation_result.get("flagged_dois", [])

    if total == 0:
        story.append(Paragraph(
            "No DOIs detected in the references section.", styles["body"]
        ))
    elif not flagged:
        story.append(Paragraph(
            f"All {total} DOI(s) verified successfully via CrossRef. \u2713",
            styles["body"],
        ))
    else:
        summary = (
            f"{verified} of {total} DOI(s) verified. "
            f"{not_found} could not be found in CrossRef."
        )
        if unreachable:
            summary += f" {unreachable} were unreachable during validation."
        story.append(Paragraph(summary, styles["body"]))
        story.append(Spacer(1, 0.1 * cm))
        story.append(Paragraph("Flagged / Unverified DOIs:", styles["label"]))
        for doi in flagged:
            story.append(Paragraph(f"\u2022 {doi}", styles["doi_flag"]))

    story.append(Spacer(1, 0.3 * cm))

    # ── SECTION 5: Verdict ────────────────────────────────────────
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#e0e0e0")
    ))
    story.append(Paragraph("Verdict", styles["section_heading"]))

    verdict_text = _generate_verdict_paragraph(
        final_score, grade, layer_scores, layer_details
    )
    story.append(Paragraph(verdict_text, styles["verdict"]))

    recommendation = RECOMMENDATION_MAP.get(grade_letter, RECOMMENDATION_MAP["F"])
    story.append(Paragraph(recommendation, styles["recommendation"]))

    # ── Build ─────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer
