import pymupdf4llm
import fitz  # PyMuPDF — fallback


def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF, with automatic fallback.

    Primary:  PyMuPDF4LLM → structured Markdown (better for section detection)
    Fallback: Plain PyMuPDF fitz.get_text() → raw text (works on more PDFs)
    """
    # ── Try PyMuPDF4LLM first (produces clean markdown) ──────────────
    try:
        md_text = pymupdf4llm.to_markdown(pdf_path)
        if len(md_text.strip()) >= 100:
            return md_text
    except Exception:
        pass  # Fall through to plain PyMuPDF

    # ── Fallback: plain PyMuPDF text extraction ──────────────────────
    print("   ⚠️  PyMuPDF4LLM failed — falling back to plain text extraction...",
          flush=True)
    try:
        doc = fitz.open(pdf_path)
        pages = [page.get_text() for page in doc]
        doc.close()
        plain_text = "\n".join(pages)
    except Exception:
        raise ValueError(
            "Could not extract text from this PDF. Please ensure it is a valid PDF file."
        )

    if len(plain_text.strip()) < 100:
        raise ValueError(
            "Could not extract meaningful text from this PDF. "
            "It may be a scanned/image-only document."
        )

    return plain_text
