"""
Unit tests for citation_checker.py — Phase 3
Tests cover: _extract_dois, check_citations (offline cases only).
_validate_doi is excluded from unit tests (requires network) — covered by UAT.
"""
import pytest
import sys
import os

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
        # Arrange — bare 10.xxxx/... without DOI: or doi.org/ prefix
        text = "version 10.3456/something-in-text-without-prefix"
        # Act
        result = citation_checker._extract_dois(text)
        # Assert
        assert result == [], f"Expected [], got {result}"

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
        assert result["total_dois"] == 0
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
        assert result["total_dois"] == 0

    def test_no_dois_in_text_returns_zero_score(self):
        # Arrange — references section but no DOIs
        text = "Smith, J. (2020). A great paper. Journal of Things, 1(1), 1-10."
        # Act
        result = citation_checker.check_citations(text)
        # Assert
        assert result["score"] == 0.0
        assert result["total_dois"] == 0

    def test_no_dois_has_correct_issue_message(self):
        # Arrange / Act
        result = citation_checker.check_citations("Smith (2020). Paper without DOIs.")
        # Assert
        assert any("No DOIs found" in issue for issue in result["issues"])

    def test_return_dict_has_all_required_keys(self):
        # Arrange
        required_keys = {
            "score", "total_dois", "verified", "not_found",
            "unreachable", "flagged_dois", "issues", "suggestions"
        }
        # Act
        result = citation_checker.check_citations("")
        # Assert
        assert required_keys.issubset(result.keys()), (
            f"Missing keys: {required_keys - result.keys()}"
        )

    def test_issues_and_suggestions_are_lists(self):
        # Arrange / Act
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
