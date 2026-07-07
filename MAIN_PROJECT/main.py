import os
import asyncio
import tempfile
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ResearchSense API is running"}

@app.get("/health")
async def health_check():
    """
    Lightweight health check — verifies server is running, keys are loaded,
    and external services are reachable. Does NOT burn Gemini API quota.
    """
    # Check Gemini keys are loaded (no API call — just check config)
    gemini_keys_loaded = len(gemini_analyzer._clients)
    any_key_configured = gemini_keys_loaded > 0

    gemini_status = {
        "gemini_keys_loaded": gemini_keys_loaded,
        "any_key_working": any_key_configured,
        "model": gemini_analyzer._MODEL,
    }

    # Check CrossRef connectivity (quick HEAD, 2s timeout)
    try:
        requests.head("https://api.crossref.org/works/10.1000/test", timeout=2)
        crossref_status = {"status": "ok"}
    except Exception:
        crossref_status = {"status": "unreachable"}

    # Check Semantic Scholar connectivity (quick HEAD, 2s timeout)
    try:
        requests.head(
            "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1",
            timeout=2,
        )
        semantic_scholar_status = {"status": "ok"}
    except Exception:
        semantic_scholar_status = {"status": "unreachable"}

    # Overall status — healthy if keys loaded and CrossRef reachable
    is_healthy = any_key_configured and crossref_status["status"] == "ok"
    overall_status = "healthy" if is_healthy else "degraded"

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

    # Save uploaded file to a temporary file
    tmp_file_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
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
async def generate_report(analysis: dict):
    """
    Accept the full /analyze JSON response body and return a downloadable PDF.
    Does NOT re-run AI analysis or CrossRef validation.
    """
    try:
        buffer = report_generator.generate_pdf_report(
            filename=analysis.get("filename", "paper.pdf"),
            layer_scores=analysis.get("layer_scores", {}),
            layer_details=analysis.get("layer_details", {}),
            final_score=analysis.get("final_score", 0.0),
            grade=analysis.get("grade", "F — Very Poor"),
            citation_result=analysis.get("citation_result", {
                "total_refs": 0, "verified": 0, "not_found": 0,
                "unreachable": 0, "flagged_dois": [], "flagged_items": [],
            }),
            detected_sections=analysis.get("detected_sections", {}),
            verdict_text=analysis.get("verdict_text", None),
            discipline=analysis.get("discipline"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "PDF generation failed", "message": str(e)}
        )

    buffer.seek(0)
    safe_name = analysis.get("filename", "report").replace(".pdf", "")
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
