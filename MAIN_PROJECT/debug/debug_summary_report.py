"""
debug_summary_report.py — Summary report generator for Phase 9 debugging.

Reads VALIDATION.json and RAW_RESULTS.json, aggregates statistics,
produces both terminal output and a DEBUG_REPORT.md markdown file.
"""

import json
import os
import sys
import time

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE_DIR, "results")
VALIDATION_PATH = os.path.join(RESULTS_DIR, "VALIDATION.json")
RAW_RESULTS_PATH = os.path.join(RESULTS_DIR, "RAW_RESULTS.json")
REPORT_PATH = os.path.join(BASE_DIR, "DEBUG_REPORT.md")


# ─── Terminal Output ──────────────────────────────────────────────────────────

def print_terminal_report(validations: list, raw_results: list):
    """Print a color-coded terminal summary."""
    # Reconfigure stdout for UTF-8 on Windows
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print(flush=True)
    print("+" + "=" * 58 + "+", flush=True)
    print("|  ResearchSense — Phase 9 Debug Summary" + " " * 19 + "|", flush=True)
    print("+" + "=" * 58 + "+", flush=True)
    print(flush=True)

    # Per-paper rows
    status_emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}

    print("  # | Status | Score  | Grade            | Category", flush=True)
    print("  " + "-" * 56, flush=True)

    for i, v in enumerate(validations, 1):
        emoji = status_emoji.get(v["status"], "?")
        score = v.get("final_score")
        score_str = f"{score:5.1f}" if score is not None else "  N/A"
        grade = v.get("grade", "N/A")
        category = v.get("category", "unknown")[:25]
        print(f"  {i} | {emoji} {v['status']:4s} | {score_str} | {grade:16s} | {category}", flush=True)

    print(flush=True)

    # Aggregate statistics
    total = len(validations)
    pass_count = sum(1 for v in validations if v["status"] == "PASS")
    warn_count = sum(1 for v in validations if v["status"] == "WARN")
    fail_count = sum(1 for v in validations if v["status"] == "FAIL")

    scores = [v["final_score"] for v in validations if v.get("final_score") is not None]
    avg_score = sum(scores) / len(scores) if scores else 0

    times = [v.get("analyze_time_ms", 0) for v in validations if v.get("analyze_time_ms", 0) > 0]
    avg_time = sum(times) / len(times) if times else 0

    total_fallback = sum(len(v.get("fallback_layers", [])) for v in validations)
    total_section_gaps = sum(len(v.get("section_gaps", [])) for v in validations)
    total_citation_gaps = sum(len(v.get("citation_gaps", [])) for v in validations)
    total_warnings = sum(len(v.get("warnings", [])) for v in validations)
    total_errors = sum(len(v.get("errors", [])) for v in validations)

    print("  +-- Aggregate Statistics --+", flush=True)
    print(f"  | Papers tested:     {total:>5} |", flush=True)
    print(f"  | PASS:              {pass_count:>5} |", flush=True)
    print(f"  | WARN:              {warn_count:>5} |", flush=True)
    print(f"  | FAIL:              {fail_count:>5} |", flush=True)
    print(f"  | Avg Score:       {avg_score:>5.1f} |", flush=True)
    print(f"  | Avg Latency:   {avg_time:>5.0f}ms |", flush=True)
    print(f"  | Fallback layers:   {total_fallback:>5} |", flush=True)
    print(f"  | Section gaps:      {total_section_gaps:>5} |", flush=True)
    print(f"  | Citation gaps:     {total_citation_gaps:>5} |", flush=True)
    print(f"  +---------------------------+", flush=True)
    print(flush=True)

    # Gaps & Issues detail
    if total_warnings > 0 or total_errors > 0:
        print("  Gaps & Issues:", flush=True)
        print("  " + "-" * 56, flush=True)
        for v in validations:
            if v.get("errors") or v.get("warnings"):
                print(f"\n  [{v['paper']}]", flush=True)
                for err in v.get("errors", []):
                    print(f"    ❌ ERROR: {err}", flush=True)
                for warn in v.get("warnings", []):
                    print(f"    ⚠️  WARN: {warn}", flush=True)
        print(flush=True)

    # Final verdict
    if fail_count > 0:
        verdict = "❌ FAILURES DETECTED"
    elif warn_count > 0:
        verdict = "⚠️  WARNINGS FOUND"
    else:
        verdict = "✅ ALL CLEAR"

    print("+" + "=" * 58 + "+", flush=True)
    print(f"|  VERDICT: {verdict}" + " " * max(0, 47 - len(verdict)) + "|", flush=True)
    print("+" + "=" * 58 + "+", flush=True)
    print(flush=True)


# ─── Markdown Report ──────────────────────────────────────────────────────────

def generate_markdown_report(validations: list, raw_results: list) -> str:
    """Generate a comprehensive DEBUG_REPORT.md."""
    lines = []

    lines.append("# ResearchSense — Phase 9 Debug Report")
    lines.append("")
    lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Papers tested:** {len(validations)}")
    lines.append("")

    # Executive summary table
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("| # | Paper | Score | Grade | Status | Time (ms) |")
    lines.append("|---|-------|-------|-------|--------|-----------|")

    for i, v in enumerate(validations, 1):
        score = v.get("final_score")
        score_str = f"{score:.1f}" if score is not None else "N/A"
        grade = v.get("grade", "N/A")
        status = v["status"]
        time_ms = v.get("analyze_time_ms", 0)
        title = v.get("title", v["paper"])[:40]
        emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(status, "?")
        lines.append(f"| {i} | {title} | {score_str} | {grade} | {emoji} {status} | {time_ms} |")

    lines.append("")

    # Aggregate statistics
    total = len(validations)
    pass_count = sum(1 for v in validations if v["status"] == "PASS")
    warn_count = sum(1 for v in validations if v["status"] == "WARN")
    fail_count = sum(1 for v in validations if v["status"] == "FAIL")

    scores = [v["final_score"] for v in validations if v.get("final_score") is not None]
    avg_score = sum(scores) / len(scores) if scores else 0

    times = [v.get("analyze_time_ms", 0) for v in validations if v.get("analyze_time_ms", 0) > 0]
    avg_time = sum(times) / len(times) if times else 0

    total_fallback = sum(len(v.get("fallback_layers", [])) for v in validations)
    total_section_gaps = sum(len(v.get("section_gaps", [])) for v in validations)
    total_citation_gaps = sum(len(v.get("citation_gaps", [])) for v in validations)

    lines.append("## Aggregate Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Papers tested | {total} |")
    lines.append(f"| PASS | {pass_count} |")
    lines.append(f"| WARN | {warn_count} |")
    lines.append(f"| FAIL | {fail_count} |")
    lines.append(f"| Average Score | {avg_score:.1f} |")
    lines.append(f"| Average Latency | {avg_time:.0f}ms |")
    lines.append(f"| Fallback layers (Gemini parse fail) | {total_fallback} |")
    lines.append(f"| Section detection gaps | {total_section_gaps} |")
    lines.append(f"| Citation detection gaps | {total_citation_gaps} |")
    lines.append("")

    # Detailed gaps section
    lines.append("## Detailed Gaps & Issues")
    lines.append("")

    has_any_issues = False

    # Section gaps
    all_section_gaps = []
    for v in validations:
        for gap in v.get("section_gaps", []):
            all_section_gaps.append({
                "paper": v["paper"],
                "section": gap["section"],
            })

    if all_section_gaps:
        has_any_issues = True
        lines.append("### Section Detection Gaps")
        lines.append("")
        lines.append("| Paper | Missing Section |")
        lines.append("|-------|-----------------|")
        for g in all_section_gaps:
            lines.append(f"| {g['paper'][:30]} | {g['section']} |")
        lines.append("")
        lines.append("> **Recommendation:** Update regex patterns in `section_detector.py` to handle")
        lines.append("> non-standard section headings (e.g., \"Background\" → \"related_work\",")
        lines.append("> \"Experimental Setup\" → \"methodology\").")
        lines.append("")

    # Citation gaps
    all_citation_gaps = []
    for v in validations:
        for gap in v.get("citation_gaps", []):
            all_citation_gaps.append({
                "paper": v["paper"],
                "gap_type": gap["gap_type"],
                "detail": gap.get("detail", ""),
            })

    if all_citation_gaps:
        has_any_issues = True
        lines.append("### Citation Detection Gaps")
        lines.append("")
        lines.append("| Paper | Gap Type | Detail |")
        lines.append("|-------|----------|--------|")
        for g in all_citation_gaps:
            lines.append(f"| {g['paper'][:30]} | {g['gap_type']} | {g['detail']} |")
        lines.append("")
        lines.append("> **Recommendation:** Update DOI regex patterns in `citation_checker.py`")
        lines.append("> to handle additional DOI formats. Consider title-based fallback")
        lines.append("> via Semantic Scholar for papers without DOIs.")
        lines.append("")

    # Fallback layers
    all_fallbacks = []
    for v in validations:
        for layer in v.get("fallback_layers", []):
            all_fallbacks.append({
                "paper": v["paper"],
                "layer": layer,
            })

    if all_fallbacks:
        has_any_issues = True
        lines.append("### Gemini Fallback Layers (Parse Failures)")
        lines.append("")
        lines.append("| Paper | Layer |")
        lines.append("|-------|-------|")
        for f in all_fallbacks:
            lines.append(f"| {f['paper'][:30]} | {f['layer']} |")
        lines.append("")
        lines.append("> **Recommendation:** Harden the Gemini prompt in `gemini_analyzer.py`")
        lines.append("> to improve JSON parsing reliability. Consider adding a third retry")
        lines.append("> with an even simpler prompt structure.")
        lines.append("")

    # Errors
    all_errors = []
    for v in validations:
        for err in v.get("errors", []):
            all_errors.append({
                "paper": v["paper"],
                "error": err,
            })

    if all_errors:
        has_any_issues = True
        lines.append("### Errors")
        lines.append("")
        for e in all_errors:
            lines.append(f"- **{e['paper']}**: {e['error']}")
        lines.append("")

    if not has_any_issues:
        lines.append("No gaps or issues detected across all papers. ✅")
        lines.append("")

    # Verdict
    if fail_count > 0:
        verdict = "❌ FAILURES DETECTED — Fix errors before demo day"
    elif warn_count > 0:
        verdict = "⚠️ WARNINGS FOUND — Review gaps but pipeline is functional"
    else:
        verdict = "✅ ALL CLEAR — Pipeline handles diverse papers correctly"

    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**{verdict}**")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by ResearchSense Phase 9 Debug Suite*")
    lines.append("")

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

def generate_report():
    """Main entry point. Produces terminal output and DEBUG_REPORT.md."""
    # Reconfigure stdout for UTF-8 on Windows
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # Load inputs
    if not os.path.exists(VALIDATION_PATH):
        print("  ✗ ERROR: VALIDATION.json not found!", flush=True)
        print("    Run debug_validate_outputs.py first.\n", flush=True)
        sys.exit(1)

    with open(VALIDATION_PATH, "r", encoding="utf-8") as f:
        validations = json.load(f)

    raw_results = []
    if os.path.exists(RAW_RESULTS_PATH):
        with open(RAW_RESULTS_PATH, "r", encoding="utf-8") as f:
            raw_results = json.load(f)

    # Terminal output
    print_terminal_report(validations, raw_results)

    # Markdown report
    md = generate_markdown_report(validations, raw_results)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"  Markdown report saved: {REPORT_PATH}", flush=True)
    print(flush=True)

    # Exit code
    fail_count = sum(1 for v in validations if v["status"] == "FAIL")
    if fail_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    generate_report()
