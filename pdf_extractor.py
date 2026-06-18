import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def extract_raw_text(pdf_path: str) -> str:
    """
    Extract raw text using Microsoft MarkItDown.
    Falls back to PyPDF if MarkItDown fails.
    """
    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        result = md.convert(pdf_path)
        return result.text_content
    except Exception as e:
        logger.error(f"MarkItDown failed for {pdf_path}: {e}")
        # Fallback to PyPDF
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e2:
            logger.error(f"PyPDF fallback failed for {pdf_path}: {e2}")
            return ""

def extract_links(pdf_path: str) -> list[str]:
    """Extracts hyperlink URIs from a PDF using pypdf."""
    links = []
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    obj = annot.get_object()
                    if obj.get("/Subtype") == "/Link":
                        uri = obj.get("/A", {}).get("/URI")
                        if uri:
                            if isinstance(uri, bytes):
                                uri = uri.decode('utf-8', 'ignore')
                            links.append(uri)
    except Exception as e:
        logger.error(f"Link extraction error for {pdf_path}: {e}")
    return list(set(links))

def trim_to_token_budget(text: str, max_chars: int = 30000) -> str:
    """Trims text to prevent API token overflow."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n...(document truncated for token efficiency)"
