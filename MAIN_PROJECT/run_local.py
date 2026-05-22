import os
import argparse
import json
import sys

# Reconfigure stdout/stderr to UTF-8 to support emojis on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Import pipeline modules
import pdf_parser
import section_detector
import gemini_analyzer
import scoring
import citation_checker
import report_generator

# Layer display names and weights for console output
LAYER_DISPLAY = {
    "structure_sections": ("01 Structure & Sections", "20%"),
    "clarity_writing":    ("02 Clarity & Writing",    "25%"),
    "methodology_rigor":  ("03 Methodology Rigor",    "25%"),
    "evidence_claims":    ("04 Evidence & Claims",    "20%"),
    "citations":          ("05 Citations & References","10%"),
}


def run_pipeline(pdf_path: str):
    """Run the entire ResearchSense pipeline on a local PDF file."""

    if not os.path.exists(pdf_path):
        print(f"❌ Error: File '{pdf_path}' not found.")
        return

    filename = os.path.basename(pdf_path)
    print(f"\n📄 Analyzing: {filename}")
    print("─" * 55)

    # ── Step 1: Extract Text ──────────────────────────────────────────
    print("⏳ [1/5] Extracting text from PDF...")
    try:
        text = pdf_parser.extract_text(pdf_path)
    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        return

    # ── Step 2: Detect Sections ───────────────────────────────────────
    print("⏳ [2/5] Detecting paper sections...")
    detection_result = section_detector.detect_sections(text)
    sections = detection_result["sections"]
    detected_sections = detection_result["detected_sections"]

    found_count = len(detected_sections)
    print(f"   ✓ Found {found_count} sections:")
    for name, confidence in detected_sections.items():
        print(f"     ✓ {name} {confidence}%")

    # ── Step 3: Multi-Layer AI Analysis ───────────────────────────────
    print("⏳ [3/5] Running multi-layer AI analysis...")
    try:
        analysis = gemini_analyzer.analyze_paper(sections)
    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        return

    # ── Step 4: Citation Check ────────────────────────────────────────
    print("⏳ [4/5] Validating citations with CrossRef...")
    citation_result = citation_checker.check_citations(
        sections.get("references", ""),
        full_text=text
    )

    # Fill citation score into analysis
    analysis["layer_scores"]["citations"] = citation_result["score"]
    analysis["layer_details"]["citations"] = {
        "score": citation_result["score"],
        "issues": citation_result["issues"],
        "suggestions": citation_result["suggestions"],
    }

    # ── Step 5: Scoring & Report ──────────────────────────────────────
    print("⏳ [5/5] Calculating final grades and generating PDF report...")
    score_result = scoring.calculate_score(analysis["layer_scores"])

    # Build report buffer
    try:
        pdf_buffer = report_generator.generate_pdf_report(
            filename=filename,
            layer_scores=analysis["layer_scores"],
            layer_details=analysis["layer_details"],
            final_score=score_result["final_score"],
            grade=score_result["grade"],
            citation_result=citation_result,
            detected_sections=detected_sections
        )
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return

    # Save PDF locally
    output_pdf_name = filename.replace('.pdf', '_report.pdf')
    with open(output_pdf_name, 'wb') as f:
        f.write(pdf_buffer.getvalue())

    # Save JSON locally
    output_json_name = filename.replace('.pdf', '_data.json')
    with open(output_json_name, 'w') as f:
        json.dump({
            "final_score": score_result["final_score"],
            "grade": score_result["grade"],
            "detected_sections": detected_sections,
            "citations": citation_result,
            "layer_scores": analysis["layer_scores"],
            "layer_details": analysis["layer_details"]
        }, f, indent=4)

    # ── Results ───────────────────────────────────────────────────────
    print("\n" + "─" * 55)
    print("  MULTI-LAYER ANALYSIS")
    print("─" * 55)
    for key, (display_name, weight) in LAYER_DISPLAY.items():
        raw_score = analysis["layer_scores"].get(key, 0)
        display_score = int(raw_score * 10)  # Convert 0-10 to 0-100
        print(f"  {display_name:<30} {weight:>5}  {display_score:>3}")
    print("─" * 55)

    print(f"\n✅ ANALYSIS COMPLETE!")
    print(f"🏆 Final Score: {score_result['final_score']} ({score_result['grade']})")
    print(f"💾 Saved PDF Report to: {output_pdf_name}")
    print(f"💾 Saved JSON Data to:  {output_json_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ResearchSense Local Tester")
    parser.add_argument("pdf_path", help="Path to the PDF file you want to analyze")
    args = parser.parse_args()

    run_pipeline(args.pdf_path)
