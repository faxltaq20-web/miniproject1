"""
debug_validate_outputs.py — Output validator & gap analyzer for Phase 9.

Reads RAW_RESULTS.json and paper metadata sidecars, runs comprehensive
validation checks (schema, score ranges, layer completeness, section gaps,
citation gaps, PDF integrity), and produces VALIDATION.json.
"""

import json
import os
import sys

# Fix Windows CP1252 encoding for Unicode output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(__file__)
PAPERS_DIR = os.path.join(BASE_DIR, "papers")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
RAW_RESULTS_PATH = os.path.join(RESULTS_DIR, "RAW_RESULTS.json")
VALIDATION_PATH = os.path.join(RESULTS_DIR, "VALIDATION.json")

# Expected response schema keys
REQUIRED_KEYS = [
    "filename", "detected_sections", "section_count", "warnings",
    "layer_scores", "layer_details", "final_score", "grade", "citation_result",
]

# Expected layer keys
LAYER_KEYS = [
    "structure_sections", "clarity_writing", "methodology_rigor",
    "evidence_claims", "citations",
]

# Valid grades
VALID_GRADES = [
    "A — Excellent",
    "B — Good",
    "C — Needs Improvement",
    "D — Poor",
    "F — Very Poor",
]

# Fallback result indicator text (from gemini_analyzer.py)
FALLBACK_INDICATOR = "Analysis unavailable — LLM returned unparseable response."


# ─── Validators ───────────────────────────────────────────────────────────────

def validate_schema(response: dict) -> tuple:
    """Check that all required top-level keys are present."""
    missing = [k for k in REQUIRED_KEYS if k not in response]
    return len(missing) == 0, missing


def validate_score_ranges(response: dict) -> tuple:
    """Check all scores are within valid ranges."""
    errors = []

    # Layer scores: 0-10
    layer_scores = response.get("layer_scores", {})
    for key, value in layer_scores.items():
        if not isinstance(value, (int, float)):
            errors.append(f"layer_scores.{key} is not a number: {value}")
        elif value < 0 or value > 10:
            errors.append(f"layer_scores.{key} out of range [0,10]: {value}")

    # Final score: 0-100
    final_score = response.get("final_score", -1)
    if not isinstance(final_score, (int, float)):
        errors.append(f"final_score is not a number: {final_score}")
    elif final_score < 0 or final_score > 100:
        errors.append(f"final_score out of range [0,100]: {final_score}")

    # Grade validity
    grade = response.get("grade", "")
    if grade not in VALID_GRADES:
        errors.append(f"Invalid grade: '{grade}' (expected one of {VALID_GRADES})")

    return len(errors) == 0, errors


def validate_layer_details(response: dict) -> tuple:
    """
    Check that each layer in layer_details has score, issues, suggestions.
    Returns (ok, fallback_layers, warnings).
    """
    warnings = []
    fallback_layers = []

    layer_details = response.get("layer_details", {})

    # Check all expected layers exist
    for key in LAYER_KEYS:
        if key not in layer_details:
            warnings.append(f"Missing layer_details entry: {key}")
            continue

        layer = layer_details[key]
        if not isinstance(layer, dict):
            warnings.append(f"layer_details.{key} is not a dict")
            continue

        # Check required sub-keys
        if "score" not in layer:
            warnings.append(f"layer_details.{key} missing 'score'")
        if "issues" not in layer:
            warnings.append(f"layer_details.{key} missing 'issues'")
        elif not isinstance(layer["issues"], list) or len(layer["issues"]) == 0:
            warnings.append(f"layer_details.{key} 'issues' is empty or not a list")
        if "suggestions" not in layer:
            warnings.append(f"layer_details.{key} missing 'suggestions'")
        elif not isinstance(layer["suggestions"], list) or len(layer["suggestions"]) == 0:
            warnings.append(f"layer_details.{key} 'suggestions' is empty or not a list")

        # Check for FALLBACK_RESULT hit
        issues = layer.get("issues", [])
        if any(FALLBACK_INDICATOR in str(issue) for issue in issues):
            fallback_layers.append(key)

        # Check for score 0 (possible analysis failure)
        score = layer.get("score", -1)
        if score == 0 and key != "citations":
            warnings.append(
                f"layer {key} returned score 0 — possible analysis failure"
            )

    ok = len(warnings) == 0 and len(fallback_layers) == 0
    return ok, fallback_layers, warnings


DISPLAY_TO_INTERNAL = {
    "Abstract": "abstract",
    "Introduction": "introduction",
    "Related Work": "related_work",
    "Methods": "methodology",
    "Results": "results",
    "Discussion": "discussion",
    "Conclusion": "conclusion",
    "References": "references"
}


def check_section_gaps(response: dict, metadata: dict) -> list:
    """
    Compare detected_sections against expected_sections from metadata.
    Returns list of gap dicts.
    """
    gaps = []
    expected = metadata.get("expected_sections", [])
    detected = response.get("detected_sections", {})

    # Normalize detected_sections keys (which are UI display names) to internal names
    if isinstance(detected, dict):
        detected_keys = {DISPLAY_TO_INTERNAL.get(k, k.lower()) for k in detected.keys()}
    elif isinstance(detected, list):
        detected_keys = {DISPLAY_TO_INTERNAL.get(k, k.lower()) for k in detected}
    else:
        detected_keys = set()

    for section in expected:
        if section not in detected_keys:
            gaps.append({
                "gap_type": "missing_section",
                "section": section,
                "expected": True,
                "detected": False,
            })

    return gaps


def check_citation_gaps(response: dict, metadata: dict) -> list:
    """
    Check for citation extraction or DOI extraction failures.
    Returns list of gap dicts.
    """
    gaps = []
    citation = response.get("citation_result", {})
    total_refs = citation.get("total_refs", 0)
    verified = citation.get("verified", 0)
    expected_ref_count = metadata.get("expected_ref_count")
    has_dois = metadata.get("has_dois", False)

    # If we expected references but found none
    if expected_ref_count and expected_ref_count > 5 and total_refs == 0:
        gaps.append({
            "gap_type": "citation_extraction_failure",
            "detail": f"Expected ~{expected_ref_count} refs but found 0",
        })

    # If paper has DOIs but none were extracted
    if has_dois and total_refs > 0 and verified == 0:
        flagged_dois = citation.get("flagged_dois", [])
        if len(flagged_dois) == 0:
            gaps.append({
                "gap_type": "doi_extraction_failure",
                "detail": f"Paper expected to have DOIs but none were extracted (total_refs={total_refs})",
            })

    return gaps


def validate_report_pdf(paper_name: str) -> tuple:
    """
    Check that the generated report PDF exists and is valid.
    Returns (ok, error_message).
    """
    pdf_path = os.path.join(RESULTS_DIR, f"{paper_name}_report.pdf")

    if not os.path.exists(pdf_path):
        return False, "Report PDF not found"

    size = os.path.getsize(pdf_path)
    if size < 5000:
        return False, f"Report PDF too small ({size} bytes, expected ≥5000)"

    # Check PDF magic bytes
    with open(pdf_path, "rb") as f:
        magic = f.read(4)
    if magic != b"%PDF":
        return False, f"Report PDF has invalid magic bytes: {magic!r}"

    return True, None


# ─── Main Validation ──────────────────────────────────────────────────────────

def validate_all():
    """
    Main entry point. Reads RAW_RESULTS.json, validates each paper's
    output, and produces VALIDATION.json.
    """
    print("=" * 60, flush=True)
    print("  ResearchSense — Phase 9 Output Validator", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    # Load RAW_RESULTS.json
    if not os.path.exists(RAW_RESULTS_PATH):
        print("  ✗ ERROR: RAW_RESULTS.json not found!", flush=True)
        print("    Run debug_run_pipeline.py first.\n", flush=True)
        sys.exit(1)

    with open(RAW_RESULTS_PATH, "r", encoding="utf-8") as f:
        raw_results = json.load(f)

    print(f"  Validating {len(raw_results)} paper results...\n", flush=True)

    validations = []

    for i, record in enumerate(raw_results, 1):
        paper_name = record.get("paper", f"unknown_{i}")
        title = record.get("title", paper_name)
        response = record.get("analyze_response")

        print(f"[{i}/{len(raw_results)}] {title[:55]}...", flush=True)

        validation = {
            "paper": paper_name,
            "title": title,
            "category": record.get("category", "unknown"),
            "analyze_status": record.get("analyze_status", 0),
            "analyze_time_ms": record.get("analyze_time_ms", 0),
            "final_score": None,
            "grade": None,
            "schema_ok": False,
            "score_ranges_ok": False,
            "layer_details_ok": False,
            "fallback_layers": [],
            "section_gaps": [],
            "citation_gaps": [],
            "report_pdf_ok": False,
            "warnings": [],
            "errors": [],
            "status": "FAIL",
        }

        # If analysis failed entirely, mark as FAIL
        if response is None:
            validation["errors"].append(
                f"Analysis failed: {record.get('error', 'unknown error')}"
            )
            print(f"   ✗ FAIL — Analysis did not return a response", flush=True)
            validations.append(validation)
            continue

        validation["final_score"] = response.get("final_score")
        validation["grade"] = response.get("grade")

        # 1. Schema validation
        schema_ok, missing_keys = validate_schema(response)
        validation["schema_ok"] = schema_ok
        if not schema_ok:
            validation["errors"].append(f"Missing schema keys: {missing_keys}")
            print(f"   ✗ Schema: missing keys {missing_keys}", flush=True)

        # 2. Score range validation
        ranges_ok, range_errors = validate_score_ranges(response)
        validation["score_ranges_ok"] = ranges_ok
        if not ranges_ok:
            for err in range_errors:
                validation["errors"].append(err)
            print(f"   ✗ Score ranges: {len(range_errors)} error(s)", flush=True)

        # 3. Layer details validation
        layers_ok, fallback_layers, layer_warnings = validate_layer_details(response)
        validation["layer_details_ok"] = layers_ok
        validation["fallback_layers"] = fallback_layers
        if fallback_layers:
            validation["warnings"].append(
                f"Fallback layers (Gemini parse failure): {fallback_layers}"
            )
            print(f"   ⚠ Fallback layers: {fallback_layers}", flush=True)
        for w in layer_warnings:
            validation["warnings"].append(w)

        # 4. Section gap analysis
        meta_path = os.path.join(PAPERS_DIR, f"{paper_name}.meta.json")
        metadata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        section_gaps = check_section_gaps(response, metadata)
        validation["section_gaps"] = section_gaps
        if section_gaps:
            gap_sections = [g["section"] for g in section_gaps]
            validation["warnings"].append(
                f"Expected sections not detected: {gap_sections}"
            )
            print(f"   ⚠ Section gaps: {gap_sections}", flush=True)

        # 5. Citation gap analysis
        citation_gaps = check_citation_gaps(response, metadata)
        validation["citation_gaps"] = citation_gaps
        if citation_gaps:
            for gap in citation_gaps:
                validation["warnings"].append(
                    f"Citation gap: {gap['gap_type']} — {gap.get('detail', '')}"
                )
            print(f"   ⚠ Citation gaps: {len(citation_gaps)}", flush=True)

        # 6. Report PDF validation
        pdf_ok, pdf_error = validate_report_pdf(paper_name)
        validation["report_pdf_ok"] = pdf_ok
        if not pdf_ok:
            validation["errors"].append(f"Report PDF: {pdf_error}")
            print(f"   ✗ Report PDF: {pdf_error}", flush=True)

        # Determine status
        has_errors = len(validation["errors"]) > 0
        has_warnings = len(validation["warnings"]) > 0

        if has_errors:
            validation["status"] = "FAIL"
            print(f"   → ❌ FAIL ({len(validation['errors'])} error(s))", flush=True)
        elif has_warnings:
            validation["status"] = "WARN"
            print(f"   → ⚠️ WARN ({len(validation['warnings'])} warning(s))", flush=True)
        else:
            validation["status"] = "PASS"
            print(f"   → ✅ PASS", flush=True)

        validations.append(validation)
        print(flush=True)

    # Write VALIDATION.json
    with open(VALIDATION_PATH, "w", encoding="utf-8") as f:
        json.dump(validations, f, indent=2)

    # Summary
    pass_count = sum(1 for v in validations if v["status"] == "PASS")
    warn_count = sum(1 for v in validations if v["status"] == "WARN")
    fail_count = sum(1 for v in validations if v["status"] == "FAIL")

    print(f"{'=' * 60}", flush=True)
    print(f"  VALIDATION COMPLETE", flush=True)
    print(f"  PASS: {pass_count}  |  WARN: {warn_count}  |  FAIL: {fail_count}", flush=True)
    print(f"  Results: {VALIDATION_PATH}", flush=True)
    print(f"{'=' * 60}\n", flush=True)


if __name__ == "__main__":
    validate_all()
