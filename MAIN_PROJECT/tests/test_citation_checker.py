"""
Unit tests for citation_checker.py — Phase 3 + Phase 7 Plan 2
Tests cover: _extract_dois, check_citations (offline cases only),
_extract_title_from_ref, _verify_title_semantic_scholar (mocked),
and parallel verification scoring tiers.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import citation_checker


# ─────────────────────────────────────────────
# Tests for _extract_dois
# ─────────────────────────────────────────────

class TestExtractDois:

    def test_empty_string_returns_empty_list(self):
        # Arrange
        text = ""
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert result == []

    def test_doi_colon_prefix_extracted(self):
        # Arrange
        text = "LeCun et al. DOI: 10.1109/5.726791"
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert "10.1109/5.726791" in result

    def test_doi_org_prefix_extracted(self):
        # Arrange
        text = "Vaswani et al. https://doi.org/10.48550/arXiv.1706.03762"
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert "10.48550/arXiv.1706.03762" in result

    def test_lowercase_doi_colon_extracted(self):
        # Arrange
        text = "Smith et al. doi: 10.1234/test.paper.2020"
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert "10.1234/test.paper.2020" in result

    def test_no_prefix_not_extracted(self):
        # Area 7: Standalone DOIs (without DOI: prefix) ARE now extracted.
        # This test verifies the enhanced DOI extraction pattern.
        text = "version 10.3456/something-in-text-without-prefix"
        # Act
        result = citation_checker._extract_dois(text)
        # Assert — standalone DOIs are now extracted
        assert "10.3456/something-in-text-without-prefix" in result

    def test_trailing_period_stripped(self):
        # Arrange
        text = "See DOI: 10.1109/5.726791."
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert result[0] == "10.1109/5.726791"
        assert result[0].endswith(".") is False

    def test_trailing_comma_stripped(self):
        # Arrange
        text = "Reference. DOI: 10.1109/5.726791,"
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert result[0] == "10.1109/5.726791"

    def test_deduplication(self):
        # Arrange — same DOI appears twice
        text = "DOI: 10.1109/5.726791\nAlso at DOI: 10.1109/5.726791"
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert result.count("10.1109/5.726791") == 1

    def test_multiple_dois_extracted(self):
        # Arrange
        text = (
            "LeCun. DOI: 10.1109/5.726791\n"
            "Vaswani. doi.org/10.48550/arXiv.1706.03762\n"
            "Smith. doi: 10.1234/test.2021"
        )
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert len(result) == 3

    def test_max_dois_cap(self):
        # Arrange — 25 unique DOIs (exceeds MAX_DOIS=20)
        lines = [f"DOI: 10.1000/test.{i:04d}" for i in range(25)]
        text = "\n".join(lines)
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert len(result) == citation_checker.MAX_DOIS


# ─────────────────────────────────────────────
# Tests for check_citations (offline — no network)
# ─────────────────────────────────────────────

class TestCheckCitationsOffline:

    def test_empty_references_text_returns_zero_score(self):
        # Arrange
        text = ""
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert result["score"] == 0.0
        assert result["total_refs"] == 0
        assert result["verified"] == 0
        assert result["not_found"] == 0
        assert result["unreachable"] == 0
        assert result["flagged_dois"] == []

    def test_empty_references_has_correct_issue_message(self):
        # Arrange / Act
        result = citation_checker.check_citations("")
        # Assert
        assert any("No references section found" in issue for issue in result["issues"])

    def test_whitespace_only_references_treated_as_empty(self):
        # Arrange
        text = "   \n\t\n   "
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert result["score"] == 0.0
        assert result["total_refs"] == 0

    def test_no_dois_in_text_returns_partial_score(self, monkeypatch):
        # Arrange — references section but no DOIs → partial credit via title verification
        monkeypatch.setattr(
            citation_checker, "_verify_references_parallel",
            lambda ref_lines, max_refs=10: {"verified": 0, "not_found": 1, "checked": 1}
        )
        text = "Smith, J. (2020). A great paper. Journal of Things, 1(1), 1-10."
        # Act
        result = citation_checker.check_citations(text)
        # Assert — 0/1 verified = ratio 0.0, score = 3.0
        assert result["score"] == 3.0
        assert result["total_refs"] >= 1

    def test_no_dois_has_correct_issue_message(self, monkeypatch):
        # Arrange / Act
        monkeypatch.setattr(
            citation_checker, "_verify_references_parallel",
            lambda ref_lines, max_refs=10: {"verified": 0, "not_found": 1, "checked": 1}
        )
        result = citation_checker.check_citations("Smith (2020). Paper without DOIs.")
        # Assert
        assert any("No DOIs found" in issue for issue in result["issues"])

    def test_return_dict_has_all_required_keys(self):
        # Arrange
        required_keys = {
            "score", "total_refs", "verified", "not_found",
            "unreachable", "flagged_dois", "flagged_items", "issues", "suggestions"
        }
        # Act
        result = citation_checker.check_citations("")
        # Assert
        assert required_keys.issubset(result.keys()), (
            f"Missing keys: {required_keys - result.keys()}"
        )

    def test_issues_and_suggestions_are_lists(self, monkeypatch):
        # Arrange / Act
        monkeypatch.setattr(
            citation_checker, "_verify_references_parallel",
            lambda ref_lines, max_refs=10: {"verified": 0, "not_found": 0, "checked": 0}
        )
        result = citation_checker.check_citations("No dois here.")
        # Assert
        assert isinstance(result["issues"], list)
        assert isinstance(result["suggestions"], list)
        assert len(result["issues"]) >= 1
        assert len(result["suggestions"]) >= 1


# ─────────────────────────────────────────────
# Tests for score calculation logic
# (using monkeypatching to avoid real CrossRef calls)
# ─────────────────────────────────────────────

class TestScoreCalculation:

    def test_all_verified_gives_score_ten(self, monkeypatch):
        # Arrange — patch _validate_doi to always return "verified"
        monkeypatch.setattr(citation_checker, "_validate_doi", lambda doi: "verified")
        text = "DOI: 10.1109/5.726791\nDOI: 10.1234/test.2020"
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert result["score"] == 10.0
        assert result["verified"] == 2
        assert result["not_found"] == 0

    def test_half_verified_gives_score_five(self, monkeypatch):
        # Arrange — patch so 1 verified, 1 not_found
        dois_seen = []
        def fake_validate(doi):
            dois_seen.append(doi)
            return "verified" if len(dois_seen) == 1 else "not_found"
        monkeypatch.setattr(citation_checker, "_validate_doi", fake_validate)
        text = "DOI: 10.1109/5.726791\nDOI: 10.9999/fake.doi"
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert result["score"] == 5.0
        assert result["verified"] == 1
        assert result["not_found"] == 1

    def test_not_found_dois_appear_in_flagged_list(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(citation_checker, "_validate_doi", lambda doi: "not_found")
        text = "DOI: 10.9999/fake.doi"
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert "10.9999/fake.doi" in result["flagged_dois"]

    def test_verified_dois_not_in_flagged_list(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(citation_checker, "_validate_doi", lambda doi: "verified")
        text = "DOI: 10.1109/5.726791"
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert result["flagged_dois"] == []

    def test_unreachable_counts_against_score(self, monkeypatch):
        # Arrange — 1 verified, 1 unreachable out of 2 → score = 1/2 * 10 = 5.0
        calls = []
        def fake_validate(doi):
            calls.append(doi)
            return "verified" if len(calls) == 1 else "unreachable"
        monkeypatch.setattr(citation_checker, "_validate_doi", fake_validate)
        text = "DOI: 10.1109/5.726791\nDOI: 10.1234/test.2020"
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert result["score"] == 5.0, f"Expected 5.0, got {result['score']}"
        assert result["unreachable"] == 1

    def test_all_unreachable_returns_special_message(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(citation_checker, "_validate_doi", lambda doi: "unreachable")
        text = "DOI: 10.1109/5.726791"
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert result["score"] == 0.0
        assert any("CrossRef API unreachable" in issue for issue in result["issues"])
        assert result["flagged_dois"] == []

    def test_score_rounded_to_one_decimal(self, monkeypatch):
        # Arrange — 1 verified out of 3 → 1/3 * 10 = 3.333... → should be 3.3
        # Note: DOI_PATTERN requires 4+ digits (10\.\d{4,}/), so use valid-format DOIs
        calls = []
        def fake_validate(doi):
            calls.append(doi)
            return "verified" if len(calls) == 1 else "not_found"
        monkeypatch.setattr(citation_checker, "_validate_doi", fake_validate)
        text = "DOI: 10.1000/test.a\nDOI: 10.2000/test.b\nDOI: 10.3000/test.c"
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert result["score"] == 3.3


# ─────────────────────────────────────────────
# Tests for _extract_title_from_ref
# ─────────────────────────────────────────────

class TestExtractTitleFromRef:

    def test_numbered_reference_with_quoted_title(self):
        # Arrange
        ref = '[1] Smith, J. (2020). "Deep Learning for NLP: A Comprehensive Survey." Journal of AI, 5(1), 12-30.'
        # Act
        result = citation_checker._extract_title_from_ref(ref)
        # Assert
        assert result == "Deep Learning for NLP: A Comprehensive Survey."

    def test_numbered_reference_without_quotes(self):
        # Arrange
        ref = '[2] Brown, T. et al. (2020). Language models are few-shot learners. NeurIPS 2020.'
        # Act
        result = citation_checker._extract_title_from_ref(ref)
        # Assert
        assert "Language models are few-shot learners" in result

    def test_dot_numbered_reference(self):
        # Arrange
        ref = '3. Johnson, M. (2019). Attention mechanisms in neural networks. ICML 2019.'
        # Act
        result = citation_checker._extract_title_from_ref(ref)
        # Assert
        assert "Attention mechanisms in neural networks" in result

    def test_strips_bracket_numbering(self):
        # Arrange
        ref = '[15] Wang, L. (2021). "Transformer architectures for vision tasks." CVPR 2021.'
        # Act
        result = citation_checker._extract_title_from_ref(ref)
        # Assert
        assert "Transformer architectures for vision tasks" in result

    def test_empty_line_returns_empty_string(self):
        # Arrange / Act
        result = citation_checker._extract_title_from_ref("")
        # Assert
        assert result == ""

    def test_short_line_returns_empty_string(self):
        # Arrange — too short to contain a meaningful title
        ref = "Smith 2020"
        # Act
        result = citation_checker._extract_title_from_ref(ref)
        # Assert
        assert result == ""

    def test_unicode_quotes_extracted(self):
        # Arrange — uses Unicode curly quotes
        ref = '[4] Lee, K. (2018). \u201cGenerative adversarial networks for image synthesis.\u201d IEEE TPAMI.'
        # Act
        result = citation_checker._extract_title_from_ref(ref)
        # Assert
        assert "Generative adversarial networks for image synthesis" in result


# ─────────────────────────────────────────────
# Tests for _verify_title_semantic_scholar (mocked)
# ─────────────────────────────────────────────

class TestVerifyTitleSemanticScholar:

    def test_returns_true_for_matching_title(self, monkeypatch):
        # Arrange — mock requests.get to return a matching title
        class FakeResponse:
            status_code = 200
            def json(self):
                return {"data": [{"title": "Attention Is All You Need"}]}

        monkeypatch.setattr("citation_checker.requests.get", lambda *args, **kwargs: FakeResponse())
        # Act
        result = citation_checker._verify_title_semantic_scholar("Attention Is All You Need")
        # Assert
        assert result is True

    def test_returns_true_for_similar_title(self, monkeypatch):
        # Arrange — returned title is slightly different but ratio >= 0.6
        class FakeResponse:
            status_code = 200
            def json(self):
                return {"data": [{"title": "Attention is All You Need"}]}

        monkeypatch.setattr("citation_checker.requests.get", lambda *args, **kwargs: FakeResponse())
        # Act
        result = citation_checker._verify_title_semantic_scholar("Attention Is All You Need")
        # Assert
        assert result is True

    def test_returns_false_for_dissimilar_title(self, monkeypatch):
        # Arrange — returned title is completely different
        class FakeResponse:
            status_code = 200
            def json(self):
                return {"data": [{"title": "Quantum Computing in Biology"}]}

        monkeypatch.setattr("citation_checker.requests.get", lambda *args, **kwargs: FakeResponse())
        # Act
        result = citation_checker._verify_title_semantic_scholar("Attention Is All You Need")
        # Assert
        assert result is False

    def test_returns_false_for_empty_results(self, monkeypatch):
        # Arrange — API returns no papers
        class FakeResponse:
            status_code = 200
            def json(self):
                return {"data": []}

        monkeypatch.setattr("citation_checker.requests.get", lambda *args, **kwargs: FakeResponse())
        # Act
        result = citation_checker._verify_title_semantic_scholar("Nonexistent Paper Title")
        # Assert
        assert result is False

    def test_returns_false_on_api_error(self, monkeypatch):
        # Arrange — API returns 500
        class FakeResponse:
            status_code = 500
            def json(self):
                return {}

        monkeypatch.setattr("citation_checker.requests.get", lambda *args, **kwargs: FakeResponse())
        # Act
        result = citation_checker._verify_title_semantic_scholar("Some Title")
        # Assert
        assert result is False

    def test_returns_false_on_timeout(self, monkeypatch):
        # Arrange — requests.get raises a timeout
        import requests as req
        monkeypatch.setattr("citation_checker.requests.get",
                            lambda *args, **kwargs: (_ for _ in ()).throw(req.Timeout("timeout")))
        # Act
        result = citation_checker._verify_title_semantic_scholar("Some Title")
        # Assert
        assert result is False

    def test_returns_false_for_empty_title(self):
        # Arrange / Act — should return False without making any API call
        result = citation_checker._verify_title_semantic_scholar("")
        # Assert
        assert result is False


# ─────────────────────────────────────────────
# Tests for parallel verification scoring tiers
# ─────────────────────────────────────────────

class TestParallelVerificationScoring:

    def test_high_verification_ratio_gives_score_ten(self, monkeypatch):
        # Arrange — 4/5 verified = 0.8 ratio → score 10.0
        monkeypatch.setattr(
            citation_checker, "_verify_references_parallel",
            lambda ref_lines, max_refs=10: {"verified": 4, "not_found": 1, "checked": 5}
        )
        refs = "\n".join([
            f"[{i}] Author{i}, A. (2020). Title of paper number {i} in the list. Journal of Testing, {i}(1), 1-10."
            for i in range(1, 6)
        ])
        # Act
        result = citation_checker.check_citations(refs)
        # Assert
        assert result["score"] == 10.0
        assert result["verified"] == 4

    def test_medium_verification_ratio_gives_score_seven(self, monkeypatch):
        # Arrange — 3/5 verified = 0.6 ratio → score 7.0
        monkeypatch.setattr(
            citation_checker, "_verify_references_parallel",
            lambda ref_lines, max_refs=10: {"verified": 3, "not_found": 2, "checked": 5}
        )
        refs = "\n".join([
            f"[{i}] Author{i}, A. (2020). Title of paper number {i} in the list. Journal of Testing, {i}(1), 1-10."
            for i in range(1, 6)
        ])
        # Act
        result = citation_checker.check_citations(refs)
        # Assert
        assert result["score"] == 7.0

    def test_low_verification_ratio_gives_score_five(self, monkeypatch):
        # Arrange — 2/5 verified = 0.4 ratio → score 5.0
        monkeypatch.setattr(
            citation_checker, "_verify_references_parallel",
            lambda ref_lines, max_refs=10: {"verified": 2, "not_found": 3, "checked": 5}
        )
        refs = "\n".join([
            f"[{i}] Author{i}, A. (2020). Title of paper number {i} in the list. Journal of Testing, {i}(1), 1-10."
            for i in range(1, 6)
        ])
        # Act
        result = citation_checker.check_citations(refs)
        # Assert
        assert result["score"] == 5.0

    def test_very_low_verification_ratio_gives_score_three(self, monkeypatch):
        # Arrange — 1/5 verified = 0.2 ratio → score 3.0
        monkeypatch.setattr(
            citation_checker, "_verify_references_parallel",
            lambda ref_lines, max_refs=10: {"verified": 1, "not_found": 4, "checked": 5}
        )
        refs = "\n".join([
            f"[{i}] Author{i}, A. (2020). Title of paper number {i} in the list. Journal of Testing, {i}(1), 1-10."
            for i in range(1, 6)
        ])
        # Act
        result = citation_checker.check_citations(refs)
        # Assert
        assert result["score"] == 3.0

    def test_no_titles_extracted_gives_minimal_credit(self, monkeypatch):
        # Arrange — no titles could be extracted
        monkeypatch.setattr(
            citation_checker, "_verify_references_parallel",
            lambda ref_lines, max_refs=10: {"verified": 0, "not_found": 0, "checked": 0}
        )
        refs = "Some long text that is not a proper reference but is more than 20 characters."
        # Act
        result = citation_checker.check_citations(refs)
        # Assert
        assert result["score"] == 3.0

    def test_verification_results_in_return_dict(self, monkeypatch):
        # Arrange — ensure verified/not_found counts propagate to result dict
        monkeypatch.setattr(
            citation_checker, "_verify_references_parallel",
            lambda ref_lines, max_refs=10: {"verified": 3, "not_found": 2, "checked": 5}
        )
        refs = "\n".join([
            f"[{i}] Author{i}, A. (2020). Title of paper number {i} in the list. Journal of Testing, {i}(1), 1-10."
            for i in range(1, 6)
        ])
        # Act
        result = citation_checker.check_citations(refs)
        # Assert
        assert result["verified"] == 3
        assert result["not_found"] == 2
