import pymupdf4llm
import fitz  # PyMuPDF — fallback
import re


def extract_hyperlink_dois(pdf_path: str) -> list:
    """Extract DOIs from PDF hyperlink annotations.

    Many academic publishers (ACL, IEEE, Springer) embed DOIs as clickable
    links on reference entries but do NOT print them in the visible text.
    Text-only extraction completely misses these.  This function scans all
    page-level link annotations for URIs containing DOI patterns and returns
    a deduplicated list.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Deduplicated list of DOI strings (e.g. ["10.18653/v1/N18-3011", ...]).
        Returns [] on any failure so the pipeline continues without DOIs.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return []

    seen = set()
    dois = []
    try:
        for page in doc:
            for link in page.get_links():
                uri = link.get("uri", "")
                if not uri:
                    continue
                # Match DOI pattern inside any URI
                m = re.search(r'(10\.\d{4,9}/[^\s,;)\]>\'"]+)', uri)
                if m:
                    doi = m.group(1).rstrip(".")
                    if doi not in seen:
                        seen.add(doi)
                        dois.append(doi)
    except Exception:
        pass
    finally:
        doc.close()

    return dois


# <<<< SCREENSHOT THIS FUNCTION for Fig 7.2.1 >>>>
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
        # sort=True orders text blocks by reading order (top-to-bottom,
        # left-to-right). Critical for two-column layouts so bibliography
        # entries are not interleaved across columns.
        pages = [page.get_text("text", sort=True) for page in doc]
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
