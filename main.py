import os
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import pipeline modules
import pdf_parser
import section_detector
import gemini_analyzer  # Phase 2
import scoring          # Phase 2
import citation_checker # Phase 3

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

@app.post("/analyze")
async def analyze_paper(file: UploadFile = File(...)):
    """
    Core processing endpoint.
    Accepts a research paper PDF, extracts text, detects sections,
    and returns a structured JSON response with detected sections and soft warnings.
    """
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

        # Detect sections using regex
        sections = section_detector.detect_sections(text)

        # Generate soft warnings for missing key sections
        warnings = []
        for s in ["abstract", "methodology", "conclusion"]:
            if not sections.get(s, "").strip():
                warnings.append(s)

        # Phase 2: Run 7-layer Gemini AI analysis
        try:
            analysis = gemini_analyzer.analyze_paper(sections)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail={"error": "Analysis service unavailable", "message": str(e)}
            )

        # Phase 3: Run citation extraction and CrossRef validation
        citation_result = citation_checker.check_citations(sections.get("references", ""))

        # Phase 3: Overwrite citations placeholder with real score
        analysis["layer_scores"]["citations"] = citation_result["score"]
        analysis["layer_details"]["citations"] = {
            "score": citation_result["score"],
            "issues": citation_result["issues"],
            "suggestions": citation_result["suggestions"],
        }

        # Calculate weighted confidence score (now includes real citations score)
        score_result = scoring.calculate_score(analysis["layer_scores"])

        # Return enriched response
        return JSONResponse(content={
            "filename": file.filename,
            "sections": sections,
            "section_count": len([v for v in sections.values() if v.strip()]),
            "warnings": warnings,
            "layer_scores": analysis["layer_scores"],
            "layer_details": analysis["layer_details"],
            "final_score": score_result["final_score"],
            "grade": score_result["grade"],
            "citation_result": {
                "total_dois": citation_result["total_dois"],
                "verified": citation_result["verified"],
                "not_found": citation_result["not_found"],
                "unreachable": citation_result["unreachable"],
                "flagged_dois": citation_result["flagged_dois"],
            },
        })

    finally:
        # Clean up temporary file
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except Exception:
                pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
