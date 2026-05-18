import pymupdf

def extract_text(pdf_path: str) -> str:
    """Extract plain text from a PDF file using PyMuPDF."""
    try:
        doc = pymupdf.open(pdf_path)
    except Exception:
        raise ValueError(
            "Could not extract text from this PDF. Please ensure it is a text-based PDF."
        )

    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    if len(text.strip()) < 100:
        raise ValueError(
            "Could not extract text from this PDF. Please ensure it is a text-based PDF."
        )

    return text
