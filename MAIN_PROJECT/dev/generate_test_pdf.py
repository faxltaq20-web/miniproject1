"""
Generate a test PDF report using mock data — no LLM or API calls needed.
Exercises the full report_generator pipeline with the new 5-layer structure.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import io
import os

# Monkey-patch the LLM call so report_generator never hits the network
import gemini_analyzer
gemini_analyzer._call_llm_with_failover = lambda prompt: (
    "The paper demonstrates solid foundational work with well-structured sections "
    "and clear methodology. However, the evidence supporting key claims needs "
    "strengthening, and several citations could not be verified against CrossRef."
)

import report_generator

# ── Mock Data ──────────────────────────────────────────────────────

mock_layer_scores = {
    "structure_sections": 8.8,   # → 88/100
    "clarity_writing":    7.9,   # → 79/100
    "methodology_rigor":  8.5,   # → 85/100
    "evidence_claims":    7.6,   # → 76/100
    "citations":          7.4,   # → 74/100
}

mock_layer_details = {
    "structure_sections": {
        "score": 8.8,
        "issues": [
            "Related Work section is missing — background context is embedded in Introduction.",
            "Discussion section is disproportionately short compared to Results.",
        ],
        "suggestions": [
            "Add a standalone Related Work / Literature Review section.",
            "Expand Discussion to interpret results in context of prior work.",
        ],
    },
    "clarity_writing": {
        "score": 7.9,
        "issues": [
            "Several sentences exceed 40 words, reducing readability.",
            "Inconsistent use of technical terminology (e.g., 'model' vs 'architecture').",
        ],
        "suggestions": [
            "Break long sentences into shorter, focused statements.",
            "Define key terms in the Introduction and use them consistently.",
        ],
    },
    "methodology_rigor": {
        "score": 8.5,
        "issues": [
            "No statistical significance tests reported for performance differences.",
            "Dataset split ratios not specified (train/val/test).",
        ],
        "suggestions": [
            "Include p-values or confidence intervals for key comparisons.",
            "Clearly state dataset partitioning strategy and random seeds.",
        ],
    },
    "evidence_claims": {
        "score": 7.6,
        "issues": [
            "Abstract claims 'state-of-the-art' but Table 2 shows only marginal improvement.",
            "Conclusion mentions 'robust generalization' without cross-dataset validation.",
        ],
        "suggestions": [
            "Qualify performance claims with specific margin of improvement.",
            "Add cross-dataset experiments or acknowledge limitation explicitly.",
        ],
    },
    "citations": {
        "score": 7.4,
        "issues": [
            "3 of 38 DOIs could not be verified (not found in CrossRef).",
            "1 duplicate reference detected.",
        ],
        "suggestions": [
            "Check flagged DOIs for typos or confirm they are published in indexed journals.",
            "Remove duplicate entries and ensure consistent formatting.",
        ],
    },
}

mock_detected_sections = {
    "Abstract": 96,
    "Introduction": 94,
    "Related Work": 89,
    "Methods": 91,
    "Results": 93,
    "Discussion": 88,
    "Conclusion": 98,
    "References": 97,
}

mock_citation_result = {
    "score": 7.4,
    "total_refs": 38,
    "verified": 35,
    "not_found": 2,
    "unreachable": 1,
    "flagged_dois": ["10.9999/fake.doi.2019", "10.8888/missing.ref"],
    "flagged_items": [
        {
            "citation": "Vaswani et al., 2017",
            "category": "duplicate",
            "detail": "Listed twice with inconsistent page ranges.",
        },
        {
            "citation": "Smith & Lee, 2019",
            "category": "not_found",
            "detail": "No CrossRef match for DOI or title search.",
        },
        {
            "citation": "Anonymous, 2020",
            "category": "missing",
            "detail": "In-text citation without bibliography entry.",
        },
    ],
    "issues": [
        "2 of 38 DOI(s) could not be verified.",
        "1 duplicate reference(s) detected.",
    ],
    "suggestions": [
        "Check flagged DOIs for typos.",
        "Remove duplicate entries.",
    ],
}

# ── Calculate final score using scoring.py ─────────────────────────
import scoring
score_result = scoring.calculate_score(mock_layer_scores)

print(f"Final Score: {score_result['final_score']} ({score_result['grade']})")
print()

# ── Generate the PDF ───────────────────────────────────────────────
print("Generating test PDF report...")

pdf_buffer = report_generator.generate_pdf_report(
    filename="sample_research_paper.pdf",
    layer_scores=mock_layer_scores,
    layer_details=mock_layer_details,
    final_score=score_result["final_score"],
    grade=score_result["grade"],
    citation_result=mock_citation_result,
    detected_sections=mock_detected_sections,
)

output_path = os.path.join(os.path.dirname(__file__), "test_report_v2.pdf")
with open(output_path, "wb") as f:
    f.write(pdf_buffer.getvalue())

print(f"Saved to: {output_path}")
print("Done!")
