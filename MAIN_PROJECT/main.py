import os
import re
import asyncio
import tempfile
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables relative to the file path
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import pipeline modules
import pdf_parser
import section_detector
import gemini_analyzer  # Phase 2
from gemini_analyzer import check_api_health, generate_verdict
import scoring          # Phase 2
import citation_checker # Phase 3
import report_generator # Phase 4

# Phase 10: Text Compression — only used here for the /compress-stats diagnostic
# endpoint. The actual compression runs inside gemini_analyzer.analyze_paper.
try:
    import text_compressor  # noqa: F401
    _COMPRESSOR_AVAILABLE = True
except ImportError:
    _COMPRESSOR_AVAILABLE = False

app = FastAPI(title="ResearchSense API", version="1.0.0")

# Upload cap — reject PDFs larger than this before reading any bytes.
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "30")) * 1024 * 1024

# CORS: comma-separated list in ALLOWED_ORIGINS, or "*" for local dev.
# Same-origin (StaticFiles-served frontend) doesn't need CORS at all; this
# only matters when the frontend is opened as a file:// or from a different host.
_origins_env = os.getenv("ALLOWED_ORIGINS", "*").strip()
_allowed_origins = ["*"] if _origins_env == "*" else [o.strip() for o in _origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Payload models ────────────────────────────────────────────────────────
class CitationResult(BaseModel):
    total_refs: int = 0
    verified: int = 0
    not_found: int = 0
    unreachable: int = 0
    flagged_dois: List[str] = Field(default_factory=list)
    flagged_items: List[Dict[str, Any]] = Field(default_factory=list)


class ReportPayload(BaseModel):
    filename: str = "paper.pdf"
    layer_scores: Dict[str, float] = Field(default_factory=dict)
    layer_details: Dict[str, Any] = Field(default_factory=dict)
    final_score: float = 0.0
    grade: str = "F — Very Poor"
    citation_result: CitationResult = Field(default_factory=CitationResult)
    detected_sections: Dict[str, Any] = Field(default_factory=dict)
    verdict_text: Optional[str] = None
    discipline: Optional[str] = None


_UNSAFE_FILENAME_CHARS = re.compile(r'[\r\n"\\/\x00-\x1f\x7f]')


def _safe_download_name(filename: str) -> str:
    """Strip control chars, quotes, path separators from a filename before
    embedding it in a Content-Disposition header."""
    base = os.path.basename(filename or "report")
    base = _UNSAFE_FILENAME_CHARS.sub("_", base)
    base = base.replace(".pdf", "").strip() or "report"
    # Absolute max: 100 chars, letters/digits/dash/underscore/dot only.
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)[:100]

def _probe(url: str) -> dict:
    try:
        requests.head(url, timeout=2)
        return {"status": "ok"}
    except Exception:
        return {"status": "unreachable"}


@app.get("/health")
async def health_check():
    """
    Lightweight health check — verifies server is running, keys are loaded,
    and external services are reachable. Does NOT burn Gemini API quota.

    Overall status is driven only by what /analyze actually depends on:
    Gemini keys must be loaded. CrossRef and Semantic Scholar are graceful
    degradation paths — an outage there doesn't break analysis, so it must
    not flip the badge to "degraded".
    """
    gemini_keys_loaded = len(gemini_analyzer._clients)
    any_key_configured = gemini_keys_loaded > 0

    gemini_status = {
        "gemini_keys_loaded": gemini_keys_loaded,
        "any_key_working": any_key_configured,
        "model": gemini_analyzer._MODEL,
    }

    # Run external probes off the event loop so /health never blocks.
    crossref_status, semantic_scholar_status = await asyncio.gather(
        asyncio.to_thread(_probe, "https://api.crossref.org/works/10.1000/test"),
        asyncio.to_thread(
            _probe,
            "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1",
        ),
    )

    overall_status = "healthy" if any_key_configured else "degraded"

    return JSONResponse(content={
        "status": overall_status,
        "gemini": gemini_status,
        "crossref": crossref_status,
        "semantic_scholar": semantic_scholar_status,
    })

@app.post("/analyze")
async def analyze_paper(file: UploadFile = File(...)):
    """
    Core processing endpoint.
    Accepts a research paper PDF, runs the full 5-layer analysis pipeline,
    and returns a structured JSON response.
    """
    # ── Pre-flight: check if any Gemini key is alive ──────────────────
    health_result = check_api_health()
    if not health_result["any_key_working"]:
        return JSONResponse(
            status_code=503,
            content={
                "error": "All Gemini API keys are unavailable. Please check your .env configuration or try again later.",
                "health": health_result,
            }
        )

    # Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are accepted"}
        )

    # Save uploaded file to a temp file, streaming in 1 MB chunks so we
    # never hold the entire body in RAM and can abort past MAX_UPLOAD_BYTES.
    tmp_file_path = ""
    try:
        total = 0
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    tmp_file.close()
                    try:
                        os.remove(tmp_file.name)
                    except Exception:
                        pass
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "File too large",
                            "message": f"PDF exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
                        },
                    )
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name

        # Extract plain text from PDF
        try:
            text = pdf_parser.extract_text(tmp_file_path)
        except ValueError:
            return JSONResponse(
                status_code=422,
                content={
                    "error": "Text extraction failed",
                    "message": "Could not extract text from this PDF. Please ensure it is a text-based PDF."
                }
            )

        # Extract DOIs from PDF hyperlink annotations (invisible in text).
        # Many publishers embed DOIs as clickable links but don't print them.
        hyperlink_dois = pdf_parser.extract_hyperlink_dois(tmp_file_path)

        # Detect sections — Tier 1 (keyword) with Tier 2 (LLM) fallback for non-standard papers
        detection_result = section_detector.detect_sections(
            text, llm_mapper=gemini_analyzer.map_headings
        )
        sections = detection_result["sections"]
        detected_sections = detection_result["detected_sections"]

        # Generate soft warnings for missing key sections
        warnings = []
        for s in ["abstract", "methodology", "conclusion"]:
            if not sections.get(s, "").strip():
                warnings.append(s)

        # Run 4-layer AI analysis AND citation check in parallel (Area 1)
        # These operate on independent data — no shared dependencies.
        try:
            analysis, citation_result = await asyncio.gather(
                asyncio.to_thread(gemini_analyzer.analyze_paper, sections),
                asyncio.to_thread(
                    citation_checker.check_citations,
                    sections.get("references", ""),
                    full_text=text,
                    pdf_hyperlink_dois=hyperlink_dois,
                ),
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail={"error": "Analysis service unavailable", "message": str(e)}
            )

        # Fill citation score into analysis
        analysis["layer_scores"]["citations"] = citation_result["score"]
        analysis["layer_details"]["citations"] = {
            "score": citation_result["score"],
            "issues": citation_result["issues"],
            "suggestions": citation_result["suggestions"],
        }

        # Calculate weighted confidence score using discipline-adaptive weights
        discipline = analysis.get("discipline", "computer_science")
        score_result = scoring.calculate_score(analysis["layer_scores"], discipline)

        # Generate verdict paragraph (moved from report_generator for parallelization)
        verdict_text = generate_verdict(
            score_result["final_score"],
            score_result["grade"],
            analysis["layer_scores"],
            analysis["layer_details"],
        )

        # Compute authoritative per-layer max marks in Python so the frontend
        # never needs to replicate the rounding logic independently.
        active_weights = scoring.DISCIPLINE_WEIGHTS.get(score_result["discipline"], scoring.WEIGHTS)
        layer_max_marks = {k: int(round(v * 100)) for k, v in active_weights.items()}

        # Return enriched response
        return JSONResponse(content={
            "filename": file.filename,
            "detected_sections": detected_sections,
            "section_count": len(detected_sections),
            "warnings": warnings,
            "layer_scores": analysis["layer_scores"],
            "layer_details": analysis["layer_details"],
            "final_score": score_result["final_score"],
            "grade": score_result["grade"],
            "discipline": score_result["discipline"],
            "layer_max_marks": layer_max_marks,
            "verdict_text": verdict_text,
            "citation_result": {
                "total_refs": citation_result.get("total_refs", 0),
                "verified": citation_result["verified"],
                "not_found": citation_result["not_found"],
                "unreachable": citation_result["unreachable"],
                "flagged_dois": citation_result["flagged_dois"],
                "flagged_items": citation_result.get("flagged_items", []),
            },
        })

    finally:
        # Clean up temporary file
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except Exception:
                pass

@app.post("/report")
async def generate_report(analysis: ReportPayload):
    """
    Accept the full /analyze JSON response body and return a downloadable PDF.
    Does NOT re-run AI analysis or CrossRef validation.
    """
    try:
        buffer = report_generator.generate_pdf_report(
            filename=analysis.filename,
            layer_scores=analysis.layer_scores,
            layer_details=analysis.layer_details,
            final_score=analysis.final_score,
            grade=analysis.grade,
            citation_result=analysis.citation_result.model_dump(),
            detected_sections=analysis.detected_sections,
            verdict_text=analysis.verdict_text,
            discipline=analysis.discipline,
        )
    except Exception:
        # Do not leak internal exception details to clients.
        raise HTTPException(status_code=500, detail="PDF generation failed")

    buffer.seek(0)
    safe_name = _safe_download_name(analysis.filename)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}_report.pdf"'
        }
    )


@app.get("/compress-stats")
async def compress_stats():
    """
    Diagnostic endpoint: returns the current COMPRESSION_MODE setting and
    whether the text_compressor module is loaded. Does not run any analysis.
    """
    mode = os.getenv("COMPRESSION_MODE", "light").strip().lower()
    return JSONResponse(content={
        "compression_mode": mode,
        "compressor_available": _COMPRESSOR_AVAILABLE,
        "description": {
            "off": "No compression — raw text sent to Gemini",
            "light": "Whitespace + citations + boilerplate + dedup (~30-55% reduction)",
            "aggressive": "light + formula/math line removal (~40-65% reduction)",
        }.get(mode, "Unknown mode"),
    })


# ── Serve the frontend (MUST be last — after all API routes) ──────────────
# Resolve path relative to this file so it works both locally and on Render.
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="static")
else:
    # Fallback: frontend may be co-located inside MAIN_PROJECT in some deploy setups
    _FRONTEND_DIR_LOCAL = Path(__file__).resolve().parent / "frontend"
    if _FRONTEND_DIR_LOCAL.exists():
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR_LOCAL), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
