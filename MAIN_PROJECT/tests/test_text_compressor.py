"""
tests/test_text_compressor.py — Unit tests for text_compressor.py (Phase 10, Approach A).

Tests cover:
  - Mode routing (off / light / aggressive)
  - Each individual normalization step
  - Public API: compress_sections() output shape and stats
  - Regression guard: reduction ≥ 20% on realistic academic text
  - Edge cases: empty input, metadata key passthrough, non-string values
"""

import re
import sys
import os
import pytest

# Ensure MAIN_PROJECT is on the path when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from text_compressor import (
    compress_sections,
    _normalize_whitespace,
    _remove_citations,
    _remove_url_noise,
    _remove_boilerplate_sentences,
    _deduplicate_sentences,
    _remove_formula_lines,
    _is_formula_line,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

REALISTIC_SECTION = (
    "In this paper, we propose a novel deep learning approach for text classification. "
    "It is worth noting that previous work has focused on shallow models. "
    "As mentioned above, the dataset consists of 10,000 samples [1, 2, 3]. "
    "In recent years, transformer-based models have achieved remarkable results. "
    "We collect data from Twitter and preprocess it using standard NLP techniques. "
    "See Figure 2 for the architecture overview. "
    "The method achieves 94.3% accuracy on the benchmark dataset. "
    "As shown in Table 1, our model outperforms all baselines. "
    "We collect data from Twitter and preprocess it using standard NLP techniques. "  # duplicate
    "In summary, we demonstrate the effectiveness of our approach. "
    "Future work will explore larger models. "
    "Details are available at https://github.com/example/repo."
)

MINIMAL_SECTIONS = {
    "abstract": "This paper proposes a new method [1]. See Figure 1 for details.",
    "introduction": "In recent years, deep learning has transformed NLP. In this paper, we apply it.",
    "methodology": "We use a dataset of 5,000 samples. The model is trained using Adam optimizer.",
}


# ─── Mode: off ────────────────────────────────────────────────────────────────

class TestOffMode:
    def test_off_mode_passthrough_text_unchanged(self):
        """mode='off' should return identical text for all sections."""
        result = compress_sections(MINIMAL_SECTIONS, mode="off")
        for key, val in MINIMAL_SECTIONS.items():
            assert result[key] == val, f"Section '{key}' was modified in off mode"

    def test_off_mode_stats_key_present(self):
        """mode='off' should still return _compression_stats key."""
        result = compress_sections(MINIMAL_SECTIONS, mode="off")
        assert "_compression_stats" in result

    def test_off_mode_reduction_pct_is_zero(self):
        """mode='off' reduction_pct must be 0.0."""
        result = compress_sections(MINIMAL_SECTIONS, mode="off")
        assert result["_compression_stats"]["reduction_pct"] == 0.0

    def test_off_mode_section_keys_preserved(self):
        """mode='off' must preserve all section keys."""
        result = compress_sections(MINIMAL_SECTIONS, mode="off")
        for key in MINIMAL_SECTIONS:
            assert key in result


# ─── Whitespace normalization ─────────────────────────────────────────────────

class TestNormalizeWhitespace:
    def test_collapses_multiple_blank_lines(self):
        text = "Para one.\n\n\n\n\nPara two."
        result = _normalize_whitespace(text)
        assert "\n\n\n" not in result
        assert "Para one." in result
        assert "Para two." in result

    def test_strips_form_feed(self):
        text = "Page one.\x0cPage two."
        result = _normalize_whitespace(text)
        assert "\x0c" not in result

    def test_removes_bom(self):
        text = "\ufeffText starts here."
        result = _normalize_whitespace(text)
        assert result.startswith("Text")

    def test_collapses_double_spaces(self):
        text = "Word   word    word."
        result = _normalize_whitespace(text)
        assert "  " not in result

    def test_normalizes_crlf(self):
        text = "Line one.\r\nLine two.\r\nLine three."
        result = _normalize_whitespace(text)
        assert "\r\n" not in result


# ─── Citation removal ─────────────────────────────────────────────────────────

class TestCitationRemoval:
    def test_bracket_single_citation_removed(self):
        result = _remove_citations("This is shown in prior work [1].")
        assert "[1]" not in result

    def test_bracket_multi_citation_removed(self):
        result = _remove_citations("Several studies [1,2,3] confirm this.")
        assert "[1,2,3]" not in result

    def test_bracket_range_citation_removed(self):
        result = _remove_citations("Multiple papers [1-5] address this.")
        assert "[1-5]" not in result

    def test_author_year_citation_removed(self):
        result = _remove_citations("As shown by Smith et al. (Smith et al., 2020), the approach works.")
        # The (Smith et al., 2020) should be removed
        assert "2020" not in result or "(Smith" not in result

    def test_text_content_preserved_after_citation_removal(self):
        result = _remove_citations("The model [1] achieves high accuracy [2,3].")
        assert "achieves high accuracy" in result

    def test_empty_brackets_cleaned_up(self):
        result = _remove_citations("Text [1] more text.")
        assert "[]" not in result


# ─── URL removal ──────────────────────────────────────────────────────────────

class TestUrlRemoval:
    def test_http_url_replaced(self):
        result = _remove_url_noise("Code is at http://example.com/repo.")
        assert "http://example.com/repo" not in result
        assert "[URL]" in result

    def test_https_url_replaced(self):
        result = _remove_url_noise("See https://arxiv.org/abs/1234.5678 for details.")
        assert "https://arxiv.org" not in result
        assert "[URL]" in result

    def test_non_url_text_preserved(self):
        result = _remove_url_noise("The method achieves 94% accuracy.")
        assert "94% accuracy" in result


# ─── Boilerplate removal ──────────────────────────────────────────────────────

class TestBoilerplateRemoval:
    def test_in_this_paper_we_removed(self):
        text = "In this paper, we propose a novel approach."
        result = _remove_boilerplate_sentences(text)
        assert "In this paper, we propose" not in result

    def test_it_is_worth_noting_removed(self):
        text = "It is worth noting that our method outperforms baselines."
        result = _remove_boilerplate_sentences(text)
        assert "It is worth noting" not in result

    def test_as_mentioned_above_removed(self):
        text = "As mentioned above, the dataset contains 5,000 samples."
        result = _remove_boilerplate_sentences(text)
        assert "As mentioned above" not in result

    def test_in_recent_years_removed(self):
        text = "In recent years, deep learning has transformed NLP."
        result = _remove_boilerplate_sentences(text)
        assert "In recent years" not in result

    def test_see_figure_removed(self):
        text = "See Figure 3 for the architecture diagram."
        result = _remove_boilerplate_sentences(text)
        assert "See Figure 3" not in result

    def test_as_shown_in_table_removed(self):
        text = "As shown in Table 2, results confirm our hypothesis."
        result = _remove_boilerplate_sentences(text)
        assert "As shown in Table 2" not in result

    def test_substantive_content_preserved(self):
        text = "The model achieves 94.3% accuracy on the test set."
        result = _remove_boilerplate_sentences(text)
        assert "94.3%" in result


# ─── Sentence deduplication ───────────────────────────────────────────────────

class TestDeduplication:
    def test_duplicate_sentence_removed(self):
        text = (
            "We collect data from Twitter. "
            "The model achieves high accuracy. "
            "We collect data from Twitter."
        )
        result = _deduplicate_sentences(text)
        # Should appear only once
        count = result.lower().count("we collect data from twitter")
        assert count == 1

    def test_unique_sentences_preserved(self):
        text = "First sentence. Second sentence. Third sentence."
        result = _deduplicate_sentences(text)
        assert "First sentence" in result
        assert "Second sentence" in result
        assert "Third sentence" in result

    def test_case_insensitive_dedup(self):
        text = "The model is fast. THE MODEL IS FAST."
        result = _deduplicate_sentences(text)
        # One of the two should be removed
        lower_count = result.lower().count("the model is fast")
        assert lower_count == 1


# ─── Formula line removal ─────────────────────────────────────────────────────

class TestFormulaLineRemoval:
    def test_pure_symbol_line_removed_in_light_mode(self):
        text = "Normal sentence.\n1234 + 5678 = 9012\nAnother sentence."
        result = _remove_formula_lines(text, aggressive=False)
        assert "1234 + 5678" not in result

    def test_alpha_lines_preserved_in_light_mode(self):
        text = "This is a normal paragraph.\nAnother normal line."
        result = _remove_formula_lines(text, aggressive=False)
        assert "This is a normal paragraph." in result
        assert "Another normal line." in result

    def test_formula_heavy_line_removed_in_aggressive(self):
        # Line with <40% alphabetic chars
        text = "Normal line.\ny = f(x) + ε ~ N(0, σ²) where ε≈0.001\nEnd line."
        result = _remove_formula_lines(text, aggressive=True)
        # The formula-heavy line should be removed
        assert "N(0, σ²)" not in result
        assert "Normal line." in result

    def test_is_formula_line_math_heavy(self):
        assert _is_formula_line("3.14159 × 10⁻⁵ ≤ 0.001") is True

    def test_is_formula_line_text_heavy(self):
        assert _is_formula_line("This is a normal English sentence.") is False

    def test_blank_lines_preserved_in_formula_removal(self):
        text = "Para one.\n\nPara two."
        result = _remove_formula_lines(text, aggressive=True)
        assert "\n\n" in result


# ─── Public API: compress_sections() ─────────────────────────────────────────

class TestCompressSectionsAPI:
    def test_compression_stats_key_present(self):
        result = compress_sections(MINIMAL_SECTIONS, mode="light")
        assert "_compression_stats" in result

    def test_all_section_keys_preserved(self):
        result = compress_sections(MINIMAL_SECTIONS, mode="light")
        for key in MINIMAL_SECTIONS:
            assert key in result

    def test_stats_contains_required_fields(self):
        result = compress_sections(MINIMAL_SECTIONS, mode="light")
        stats = result["_compression_stats"]
        assert "mode" in stats
        assert "total_original_chars" in stats
        assert "total_compressed_chars" in stats
        assert "reduction_pct" in stats
        assert "per_section" in stats

    def test_per_section_stats_populated(self):
        result = compress_sections(MINIMAL_SECTIONS, mode="light")
        per_section = result["_compression_stats"]["per_section"]
        for key in MINIMAL_SECTIONS:
            assert key in per_section

    def test_metadata_key_passthrough(self):
        """Section keys starting with '_' must not be compressed or included in stats."""
        sections = {"abstract": "Text here.", "_meta": {"version": 1}}
        result = compress_sections(sections, mode="light")
        assert result["_meta"] == {"version": 1}
        assert "_meta" not in result["_compression_stats"]["per_section"]

    def test_references_section_not_compressed(self):
        """References section must pass through unmodified — citation_checker needs raw text."""
        refs = "1. Smith, J. et al. (2020). Paper title. Journal, 10(2), 1-10. DOI:10.1000/xyz"
        sections = {"abstract": "This paper proposes a new method [1].", "references": refs}
        result = compress_sections(sections, mode="light")
        # References must be byte-identical to input
        assert result["references"] == refs
        # References must NOT appear in compression stats (not counted)
        assert "references" not in result["_compression_stats"]["per_section"]

    def test_non_string_value_passthrough(self):
        """Non-string section values (e.g. None, int) must pass through unchanged."""
        sections = {"abstract": "Some text.", "count": 42}
        result = compress_sections(sections, mode="light")
        assert result["count"] == 42

    def test_empty_sections_dict(self):
        """Empty dict should return empty dict with zeroed stats."""
        result = compress_sections({}, mode="light")
        assert result["_compression_stats"]["total_original_chars"] == 0
        assert result["_compression_stats"]["reduction_pct"] == 0.0

    def test_invalid_mode_falls_back_to_light(self, capsys):
        """Invalid mode string should fall back to 'light' without crashing."""
        result = compress_sections(MINIMAL_SECTIONS, mode="invalid_mode")
        # Should complete without exception
        assert "_compression_stats" in result


# ─── Regression guard: realistic reduction ───────────────────────────────────

class TestReductionRegression:
    def test_light_mode_reduces_realistic_text_by_at_least_20_pct(self):
        """
        Regression guard: compression must achieve ≥20% reduction on realistic
        academic text with citations, boilerplate, URLs, and duplicates.
        """
        sections = {"methodology": REALISTIC_SECTION}
        result = compress_sections(sections, mode="light")
        stats = result["_compression_stats"]
        reduction = stats["reduction_pct"]
        assert reduction >= 20.0, (
            f"Expected ≥20% reduction, got {reduction}%. "
            f"Original: {stats['total_original_chars']} chars, "
            f"Compressed: {stats['total_compressed_chars']} chars"
        )

    def test_no_section_grows_after_compression(self):
        """Compression must never make a section larger than the original."""
        result = compress_sections(MINIMAL_SECTIONS, mode="light")
        per_section = result["_compression_stats"]["per_section"]
        for key, s in per_section.items():
            assert s["compressed"] <= s["original"], (
                f"Section '{key}' grew after compression: "
                f"{s['original']} → {s['compressed']} chars"
            )

    def test_aggressive_mode_reduces_more_than_light(self):
        """Aggressive mode must produce equal or shorter output than light mode."""
        sections = {"methodology": REALISTIC_SECTION}
        light_result = compress_sections(sections, mode="light")
        agg_result = compress_sections(sections, mode="aggressive")
        light_chars = light_result["_compression_stats"]["total_compressed_chars"]
        agg_chars = agg_result["_compression_stats"]["total_compressed_chars"]
        assert agg_chars <= light_chars, (
            f"Aggressive ({agg_chars}) should be ≤ light ({light_chars})"
        )
