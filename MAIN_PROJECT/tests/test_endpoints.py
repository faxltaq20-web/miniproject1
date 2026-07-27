"""
Integration tests for main.py endpoints — Phase 14 hardening.

Uses FastAPI TestClient and monkeypatches the AI + external calls so we
can exercise `/analyze` → `/report` round-trip without hitting Gemini,
CrossRef, or Semantic Scholar.
"""
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

import main
import gemini_analyzer
import citation_checker
import pdf_parser
import section_detector


# ── Stub fixtures ─────────────────────────────────────────────────────────

_FAKE_ANALYSIS = {
    "layer_scores": {
        "structure_sections": 8.0,
        "clarity_writing":    7.5,
        "methodology_rigor":  7.0,
        "evidence_claims":    7.0,
        "citations":          0.0,   # filled by citation stub
    },
    "layer_details": {
        "structure_sections": {"score": 8.0, "issues": [], "suggestions": []},
        "clarity_writing":    {"score": 7.5, "issues": ["passive voice"], "suggestions": ["rewrite"]},
        "methodology_rigor":  {"score": 7.0, "issues": [], "suggestions": []},
        "evidence_claims":    {"score": 7.0, "issues": [], "suggestions": []},
    },
    "discipline": "computer_science",
}

_FAKE_CITATIONS = {
    "score": 8.0,
    "issues": [],
    "suggestions": [],
    "total_refs": 4,
    "verified": 3,
    "not_found": 1,
    "unreachable": 0,
    "flagged_dois": ["10.9999/not-a-real-doi"],
    "flagged_items": [],
}


@pytest.fixture
def client(monkeypatch):
    # Silence real Gemini + citation + PDF work
    monkeypatch.setattr(pdf_parser, "extract_text", lambda p: "Abstract\nThis paper...\nReferences\n[1] Foo.")
    monkeypatch.setattr(pdf_parser, "extract_hyperlink_dois", lambda p: [])
    monkeypatch.setattr(
        section_detector, "detect_sections",
        lambda text, llm_mapper=None: {
            "sections": {"abstract": "x", "methodology": "y", "conclusion": "z", "references": "[1] Foo."},
            "detected_sections": {"Abstract": 1, "References": 5},
        },
    )
    monkeypatch.setattr(gemini_analyzer, "analyze_paper", lambda sections: _FAKE_ANALYSIS)
    monkeypatch.setattr(
        gemini_analyzer, "check_api_health",
        lambda: {"any_key_working": True, "keys": [{"working": True}]},
    )
    monkeypatch.setattr(
        gemini_analyzer, "generate_verdict",
        lambda score, grade, ls, ld: "Solid paper with minor style issues.",
    )
    monkeypatch.setattr(
        citation_checker, "check_citations",
        lambda refs, full_text="", pdf_hyperlink_dois=None: _FAKE_CITATIONS,
    )
    return TestClient(main.app)


# ── Endpoint tests ────────────────────────────────────────────────────────

class TestHealthEndpoint:

    def test_health_returns_200_and_schema(self, client, monkeypatch):
        # Stub external probes so we don't touch the network
        monkeypatch.setattr(main, "_probe", lambda url: {"status": "ok"})
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert "gemini" in body
        assert body["gemini"]["any_key_working"] is True
        assert body["crossref"]["status"] == "ok"

    def test_health_stays_healthy_when_crossref_down(self, client, monkeypatch):
        # Regression: previously, CrossRef outage flipped status to degraded
        # even though /analyze still works.
        monkeypatch.setattr(main, "_probe", lambda url: {"status": "unreachable"})
        body = client.get("/health").json()
        assert body["status"] == "healthy"


class TestAnalyzeEndpoint:

    def test_rejects_non_pdf_extension(self, client):
        r = client.post("/analyze", files={"file": ("a.txt", b"hi", "text/plain")})
        assert r.status_code == 400
        assert "PDF" in r.json()["error"]

    def test_rejects_oversized_upload(self, client, monkeypatch):
        # Shrink the cap so we don't have to allocate 30 MB in RAM.
        monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", 1024)
        payload = b"x" * 4096
        r = client.post("/analyze", files={"file": ("big.pdf", payload, "application/pdf")})
        assert r.status_code == 413
        assert "too large" in r.json()["error"].lower()

    def test_happy_path_returns_full_schema(self, client):
        r = client.post(
            "/analyze",
            files={"file": ("paper.pdf", b"%PDF-1.4 stub", "application/pdf")},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # Schema contract that the frontend relies on
        for key in ("filename", "final_score", "grade", "discipline",
                    "layer_scores", "layer_details", "layer_max_marks",
                    "verdict_text", "citation_result"):
            assert key in body, f"missing {key} in response"
        assert body["final_score"] > 0
        assert body["citation_result"]["verified"] == 3


class TestReportEndpoint:

    def _minimal_payload(self):
        return {
            "filename": "paper.pdf",
            "layer_scores": {
                "structure_sections": 8.0, "clarity_writing": 7.5,
                "methodology_rigor": 7.0, "evidence_claims": 7.0, "citations": 8.0,
            },
            "layer_details": {
                "structure_sections": {"score": 8.0, "issues": [], "suggestions": []},
                "clarity_writing":    {"score": 7.5, "issues": [], "suggestions": []},
                "methodology_rigor":  {"score": 7.0, "issues": [], "suggestions": []},
                "evidence_claims":    {"score": 7.0, "issues": [], "suggestions": []},
                "citations":          {"score": 8.0, "issues": [], "suggestions": []},
            },
            "final_score": 76.0,
            "grade": "B — Good",
            "citation_result": {
                "total_refs": 4, "verified": 3, "not_found": 1,
                "unreachable": 0, "flagged_dois": [], "flagged_items": [],
            },
            "detected_sections": {"Abstract": 1},
            "verdict_text": "Solid work.",
            "discipline": "computer_science",
        }

    def test_report_generates_pdf(self, client):
        r = client.post("/report", json=self._minimal_payload())
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:4] == b"%PDF"

    def test_report_filename_is_sanitized(self, client):
        payload = self._minimal_payload()
        payload["filename"] = '../../etc/passwd\r\ninject.pdf'
        r = client.post("/report", json=payload)
        assert r.status_code == 200
        cd = r.headers["content-disposition"]
        assert "\r" not in cd
        assert "\n" not in cd
        assert "../" not in cd

    def test_report_rejects_invalid_payload(self, client):
        # final_score as non-numeric string should fail Pydantic validation
        r = client.post("/report", json={"final_score": "not-a-number"})
        assert r.status_code == 422


class TestAnalyzeReportRoundTrip:

    def test_round_trip(self, client):
        analyze = client.post(
            "/analyze",
            files={"file": ("paper.pdf", b"%PDF-1.4 stub", "application/pdf")},
        )
        assert analyze.status_code == 200
        report = client.post("/report", json=analyze.json())
        assert report.status_code == 200
        assert report.content[:4] == b"%PDF"


class TestFilenameSanitizer:

    @pytest.mark.parametrize("dirty,expected_contains", [
        ("normal.pdf",                "normal"),
        ("../../etc/passwd",          "passwd"),
        ('with"quote.pdf',            "with_quote"),
        ("with\r\nnewline.pdf",       "with__newline"),
        ("",                          "report"),
    ])
    def test_safe_download_name(self, dirty, expected_contains):
        out = main._safe_download_name(dirty)
        assert expected_contains in out
        for bad in ('"', "\r", "\n", "\\", "/"):
            assert bad not in out
