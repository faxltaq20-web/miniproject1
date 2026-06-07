import os
import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Reconfigure stdout/stderr to UTF-8 to support emojis on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Load .env so COMPRESSION_MODE and other settings are available
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path)

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


def save_file_safely(base_name: str, content, is_binary: bool = True) -> str:
    """Saves content to base_name. If base_name is locked (PermissionError),
    appends a numeric suffix (_v1, _v2, etc.) until it can write successfully.
    Returns the actual filename written."""
    name, ext = os.path.splitext(base_name)
    suffix = 0
    while True:
        curr_name = f"{name}_v{suffix}{ext}" if suffix > 0 else base_name
        try:
            mode = 'wb' if is_binary else 'w'
            with open(curr_name, mode) as f:
                if is_binary:
                    f.write(content)
                else:
                    json.dump(content, f, indent=4)
            return curr_name
        except PermissionError:
            suffix += 1
            if suffix > 20: # cap to prevent infinite loop
                raise


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

    # ── Step 3: Multi-Layer AI Analysis ───────────────────────────────────
    _cmode = os.getenv("COMPRESSION_MODE", "light")
    print(f"⏳ [3/5] Running multi-layer AI analysis... (compression={_cmode})")
    try:
        analysis = gemini_analyzer.analyze_paper(sections)
    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        return

    # ── Step 4: Citation Check ──────────────────────────────────────────
    print("⏳ [4/5] Validating citations with CrossRef...")
    # NOTE: `sections` here is the ORIGINAL dict — analyze_paper() compresses
    # a local copy only, so sections["references"] is always raw/uncompressed.
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

    # Save PDF locally with lock protection
    pdf_base_name = filename.replace('.pdf', '_report.pdf')
    try:
        output_pdf_name = save_file_safely(pdf_base_name, pdf_buffer.getvalue(), is_binary=True)
        if output_pdf_name != pdf_base_name:
            print(f"⚠️  Warning: '{pdf_base_name}' was locked. Saved as '{output_pdf_name}' instead.")
    except Exception as e:
        print(f"❌ Failed to save PDF: {e}")
        output_pdf_name = "None"

    # Save JSON locally with lock protection
    json_base_name = filename.replace('.pdf', '_data.json')
    try:
        json_data = {
            "final_score": score_result["final_score"],
            "grade": score_result["grade"],
            "detected_sections": detected_sections,
            "citations": citation_result,
            "layer_scores": analysis["layer_scores"],
            "layer_details": analysis["layer_details"]
        }
        output_json_name = save_file_safely(json_base_name, json_data, is_binary=False)
        if output_json_name != json_base_name:
            print(f"⚠️  Warning: '{json_base_name}' was locked. Saved as '{output_json_name}' instead.")
    except Exception as e:
        print(f"❌ Failed to save JSON data: {e}")
        output_json_name = "None"

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
