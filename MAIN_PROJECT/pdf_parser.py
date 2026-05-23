import pymupdf4llm

def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF as Markdown using PyMuPDF4LLM.
    
    Returns structured markdown with ## headings, tables, and formatting
    preserved — much better for section detection and LLM analysis.
    """
    try:
        md_text = pymupdf4llm.to_markdown(pdf_path)
    except Exception:
        raise ValueError(
            "Could not extract text from this PDF. Please ensure it is a valid PDF file."
        )

    if len(md_text.strip()) < 100:
        raise ValueError(
            "Could not extract text from this PDF. Please ensure it is a text-based PDF."
        )

    return md_text
