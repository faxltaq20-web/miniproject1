"""
validate_compression.py — Validation Harness for Phase 10 Approach A.

Measures:
  (a) Token/char reduction achieved by text_compressor on real paper sections
  (b) Score drift when Gemini analyzes compressed vs. uncompressed text (optional, requires API)

Usage:
    python validate_compression.py                   # reduction table only (offline)
    python validate_compression.py --score-drift     # also runs Gemini analysis (uses API quota)
    python validate_compression.py --mode aggressive # test a specific mode

Output:
    Console: formatted table
    File:    debug/compression_validation_report.txt
"""

import sys
import os
import json
import argparse
import time

sys.path.insert(0, os.path.dirname(__file__))

from text_compressor import compress_sections

# ── Output directory ──────────────────────────────────────────────────────────
DEBUG_DIR = os.path.join(os.path.dirname(__file__), "debug")
os.makedirs(DEBUG_DIR, exist_ok=True)
REPORT_FILE = os.path.join(DEBUG_DIR, "compression_validation_report.txt")


# ── Sample paper sections (built-in — no PDF needed for offline validation) ──
# These are representative academic paper excerpts with common patterns
# that compression should handle: citations, boilerplate, URLs, duplicates.
SAMPLE_PAPERS = {
    "paper_1_transformer": {
        "abstract": (
            "In this paper, we propose a new simple network architecture, the Transformer, "
            "based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. "
            "As mentioned above, experiments on two machine translation tasks show these models "
            "to be superior in quality while being more parallelizable and requiring significantly "
            "less time to train [1, 2, 3]. It is worth noting that our model achieves 28.4 BLEU "
            "on the WMT 2014 English-to-German translation task. As shown in Table 1, this "
            "improves over the existing best results, including ensembles, by over 2 BLEU [4, 5]. "
            "Details are available at https://github.com/tensorflow/tensor2tensor."
        ),
        "introduction": (
            "Recurrent neural networks, long short-term memory [1] and gated recurrent [2] neural "
            "networks in particular, have been firmly established as state of the art approaches "
            "in sequence modeling and transduction problems such as language modeling and "
            "machine translation. In this paper, we present the Transformer, a model architecture "
            "that avoids recurrence entirely and instead relies on an attention mechanism to draw "
            "global dependencies between input and output. In recent years, numerous efforts "
            "have since sought to reduce sequential computation (Smith et al., 2017), (Jones, 2018). "
            "As mentioned above, the fundamental constraint of sequential computation, however, "
            "remains. It is worth noting that attention mechanisms have become an integral part "
            "of compelling sequence modeling and transduction models. "
            "Recurrent neural networks, long short-term memory and gated recurrent neural networks "
            "have been firmly established as state of the art approaches in sequence modeling."
        ),
        "methodology": (
            "The Transformer uses stacked self-attention and point-wise, fully connected layers "
            "for both the encoder and decoder, shown in the left and right halves of Figure 1, "
            "respectively. See Figure 1 for the encoder structure. "
            "Encoder: The encoder is composed of a stack of N = 6 identical layers. "
            "Each layer has two sub-layers. The first is a multi-head self-attention mechanism, "
            "and the second is a simple, position-wise fully connected feed-forward network [6]. "
            "We employ a residual connection (He et al., 2016) around each of the two sub-layers, "
            "followed by layer normalization. As described above, that is, the output of each "
            "sub-layer is LayerNorm(x + Sublayer(x)). See Table 2 for hyperparameter settings. "
            "In this paper, we use the Adam optimizer with β₁ = 0.9, β₂ = 0.98. "
            "The model was trained using 8 NVIDIA P100 GPUs. "
            "Further implementation details are at https://arxiv.org/abs/1706.03762."
        ),
        "results": (
            "On the WMT 2014 English-to-German translation task, the big transformer model "
            "outperforms the best previously reported models, including ensembles [7], by more "
            "than 2.0 BLEU, establishing a new state-of-the-art BLEU score of 28.4. "
            "As shown in Table 2, the big transformer model achieves 41.0 BLEU on the "
            "WMT 2014 English-to-French translation task [8, 9, 10]. "
            "As mentioned above, training took 3.5 days on eight P100 GPUs. "
            "This is a small fraction of the training costs of the best models from the "
            "literature (Smith et al., 2019). In this paper, we demonstrate superior results. "
            "In summary, we show that transformer models outperform all baselines. "
            "The model achieves 28.4 BLEU on English-German translation task."
        ),
        "conclusion": (
            "In this work, we presented the Transformer, the first sequence transduction model "
            "based entirely on attention, replacing the recurrent layers most commonly used in "
            "encoder-decoder architectures with multi-headed self-attention. "
            "To the best of our knowledge, this is the first purely attentional model for "
            "sequence transduction. In summary, we demonstrate that the Transformer achieves "
            "superior quality while being more parallelizable. As mentioned above, the model "
            "trains significantly faster than architectures based on recurrent or convolutional "
            "layers. We are excited about the future of attention-based models and plan to apply "
            "them to other tasks. Code is available at https://github.com/tensorflow/tensor2tensor."
        ),
    },
    "paper_2_ml_classification": {
        "abstract": (
            "In recent years, deep learning has revolutionized natural language processing. "
            "In this paper, we propose a BERT-based approach for document classification. "
            "It should be noted that previous approaches relied on bag-of-words features. "
            "Our model achieves 95.2% F1 score on the benchmark [1, 2]. "
            "Code available at https://github.com/example/bert-classify."
        ),
        "methodology": (
            "We fine-tune BERT (Devlin et al., 2019) on a classification task. "
            "As shown in Figure 2, the architecture consists of a transformer encoder. "
            "The dataset contains 50,000 labeled documents (Jones et al., 2020). "
            "We use a batch size of 32 and learning rate of 2e-5. "
            "As mentioned above, we split the data into 80/10/10 train/dev/test. "
            "In this paper, we use cross-entropy loss. "
            "Fine-tuning is performed for 3 epochs on 4 Tesla V100 GPUs. "
            "See Table 3 for hyperparameter details."
        ),
        "results": (
            "Our model achieves 95.2% F1 score on the test set. "
            "As shown in Table 1, this outperforms all baseline methods [3, 4, 5]. "
            "The improvement over the previous state-of-the-art is 3.1% F1. "
            "In summary, we demonstrate that BERT fine-tuning is highly effective. "
            "Our model achieves 95.2% F1 score on the test set."  # duplicate
        ),
    },
}

# ── Helper: load from cached JSON if available ────────────────────────────────
def _try_load_cached_paper(json_path: str) -> dict:
    """Load section-like dict from a cached paper JSON if it has 'sections' key."""
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        if "sections" in data:
            return data["sections"]
    except Exception:
        pass
    return {}


# ── Reduction table ───────────────────────────────────────────────────────────
def run_reduction_analysis(mode: str = "light") -> dict:
    """Run compression on all sample papers, print per-section and overall stats."""
    all_results = {}
    lines = []

    lines.append("=" * 72)
    lines.append(f"COMPRESSION VALIDATION REPORT — mode='{mode}'")
    lines.append("=" * 72)

    total_orig_all = 0
    total_comp_all = 0

    for paper_id, sections in SAMPLE_PAPERS.items():
        lines.append(f"\n{'─'*72}")
        lines.append(f"  Paper: {paper_id}")
        lines.append(f"{'─'*72}")
        lines.append(f"  {'Section':<20} {'Original':>10} {'Compressed':>12} {'Reduction':>10}")
        lines.append(f"  {'─'*20} {'─'*10} {'─'*12} {'─'*10}")

        result = compress_sections(sections, mode=mode)
        stats = result["_compression_stats"]

        for section_key, s in stats["per_section"].items():
            lines.append(
                f"  {section_key:<20} {s['original']:>10,} {s['compressed']:>12,} {s['pct']:>9.1f}%"
            )

        orig = stats["total_original_chars"]
        comp = stats["total_compressed_chars"]
        pct  = stats["reduction_pct"]
        lines.append(f"  {'─'*20} {'─'*10} {'─'*12} {'─'*10}")
        lines.append(f"  {'TOTAL':<20} {orig:>10,} {comp:>12,} {pct:>9.1f}%")

        all_results[paper_id] = stats
        total_orig_all += orig
        total_comp_all += comp

        # Assertion guard
        for section_key, s in stats["per_section"].items():
            if s["compressed"] > s["original"]:
                lines.append(f"  !! WARNING: '{section_key}' GREW after compression!")

    # Overall summary
    overall_pct = round((1 - total_comp_all / total_orig_all) * 100, 1) if total_orig_all > 0 else 0.0
    lines.append(f"\n{'='*72}")
    lines.append(f"  OVERALL SUMMARY")
    lines.append(f"{'='*72}")
    lines.append(f"  Mode             : {mode}")
    lines.append(f"  Papers tested    : {len(SAMPLE_PAPERS)}")
    lines.append(f"  Total original   : {total_orig_all:,} chars")
    lines.append(f"  Total compressed : {total_comp_all:,} chars")
    lines.append(f"  Overall reduction: {overall_pct:.1f}%")
    lines.append("")

    if overall_pct >= 20:
        lines.append(f"  ✓ PASS: Reduction {overall_pct:.1f}% meets ≥20% threshold")
    else:
        lines.append(f"  ✗ FAIL: Reduction {overall_pct:.1f}% is below ≥20% threshold!")

    lines.append("=" * 72)

    report_text = "\n".join(lines)
    print(report_text)

    # Write to file
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n  Report saved → {REPORT_FILE}")

    return all_results


# ── Score drift (optional — requires live Gemini) ─────────────────────────────
def run_score_drift_analysis(paper_id: str = "paper_1_transformer", mode: str = "light"):
    """
    Compare Gemini scores on original vs. compressed sections.
    REQUIRES active GEMINI API key and will consume 2 RPD per run.
    """
    try:
        import gemini_analyzer
    except ImportError as e:
        print(f"  [Score Drift] Cannot import gemini_analyzer: {e}")
        return

    sections = SAMPLE_PAPERS.get(paper_id)
    if not sections:
        print(f"  [Score Drift] Paper '{paper_id}' not found.")
        return

    print(f"\n{'─'*72}")
    print(f"  Score Drift Analysis — paper='{paper_id}', mode='{mode}'")
    print(f"  (This uses 2 Gemini API calls — uncompressed + compressed)")
    print(f"{'─'*72}")

    # Uncompressed
    print("  Running Gemini on ORIGINAL sections...")
    orig_result = gemini_analyzer.analyze_paper(dict(sections))
    orig_scores = orig_result.get("layer_scores", {})
    time.sleep(5)  # be polite to rate limits

    # Compressed
    compressed = compress_sections(dict(sections), mode=mode)
    compressed.pop("_compression_stats", {})
    print(f"  Running Gemini on COMPRESSED sections (mode={mode})...")
    comp_result = gemini_analyzer.analyze_paper(compressed)
    comp_scores = comp_result.get("layer_scores", {})

    # Diff table
    print(f"\n  {'Layer':<25} {'Original':>10} {'Compressed':>12} {'Delta':>8} {'Status':>8}")
    print(f"  {'─'*25} {'─'*10} {'─'*12} {'─'*8} {'─'*8}")

    max_delta = 0.0
    drift_lines = []
    for layer in orig_scores:
        o = orig_scores.get(layer, 0.0)
        c = comp_scores.get(layer, 0.0)
        delta = abs(c - o)
        max_delta = max(max_delta, delta)
        status = "✓ OK" if delta <= 0.5 else "⚠ DRIFT"
        row = f"  {layer:<25} {o:>10.1f} {c:>12.1f} {delta:>8.2f} {status:>8}"
        print(row)
        drift_lines.append(row)

    print(f"\n  Max delta: {max_delta:.2f} (threshold: 0.5)")
    if max_delta <= 0.5:
        print("  ✓ PASS: Score drift within acceptable ±0.5 threshold")
    else:
        print("  ⚠ WARNING: Score drift exceeds ±0.5 threshold!")

    # Append to report file
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\nSCORE DRIFT — paper='{paper_id}', mode='{mode}'\n")
        f.write("\n".join(drift_lines))
        f.write(f"\nMax delta: {max_delta:.2f}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Validate text_compressor reduction and score drift")
    parser.add_argument("--mode", default="light", choices=["light", "aggressive"],
                        help="Compression mode to test (default: light)")
    parser.add_argument("--score-drift", action="store_true",
                        help="Also run Gemini score drift analysis (uses API quota)")
    parser.add_argument("--paper", default="paper_1_transformer",
                        help="Paper ID for score drift analysis")
    args = parser.parse_args()

    # 1. Reduction table (always runs, offline)
    run_reduction_analysis(mode=args.mode)

    # 2. Score drift (optional)
    if args.score_drift:
        run_score_drift_analysis(paper_id=args.paper, mode=args.mode)


if __name__ == "__main__":
    main()
