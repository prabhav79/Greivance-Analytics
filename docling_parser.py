"""
docling_parser.py
-----------------
Structured PDF extraction for ATR (Action Taken Report) files using docling.

WHY: pypdf returns flat, unordered text that mixes headers, body text, and table
cells. Docling uses a layout model to reconstruct reading order, detect section
headers, and export clean Markdown — giving the Gemini API less noise to wade
through, reducing token consumption by ~50-60%, and improving JSON extraction
accuracy.

CACHING: Each PDF is converted once and the resulting Markdown is saved to
output/parsed_cache/<stem>.md. Subsequent calls reuse the cached file, so
batch re-runs don't incur the ~3-8s per-file ML cost again.

FALLBACK: If docling is unavailable or fails (e.g. corrupt PDF), the module
transparently falls back to pypdf so the existing pipeline never breaks.
"""

import os
import re
import logging
from pathlib import Path

# ── Windows: disable HuggingFace symlinks to avoid WinError 1314 ─────────────
# On Windows without Developer Mode, HF Hub tries to create symlinks in its
# model cache and fails with "A required privilege is not held by the client".
# Setting HF_HUB_DISABLE_SYMLINKS=1 forces file copies instead — slightly more
# disk space but works without needing elevated privileges or Developer Mode.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HUGGINGFACE_HUB_VERBOSITY", "warning")

logger = logging.getLogger(__name__)

# ── Cache directory (sits next to the output/ folder) ─────────────────────────
_SCRIPT_DIR = Path(__file__).parent
CACHE_DIR = _SCRIPT_DIR / "output" / "parsed_cache"

# ── Docling availability check ─────────────────────────────────────────────────
try:
    from docling.document_converter import DocumentConverter
    _DOCLING_AVAILABLE = True
    logger.info("docling is available — structured parsing enabled.")
except ImportError:
    _DOCLING_AVAILABLE = False
    logger.warning("docling not found — falling back to pypdf for all PDFs.")


def _get_cache_path(pdf_path: str) -> Path:
    """Returns the expected cache path for a given PDF."""
    stem = Path(pdf_path).stem
    return CACHE_DIR / f"{stem}.md"


def _load_from_cache(pdf_path: str) -> str | None:
    """Returns cached Markdown if it exists, else None."""
    cache_path = _get_cache_path(pdf_path)
    if cache_path.exists():
        logger.info(f"Cache hit: {cache_path.name}")
        return cache_path.read_text(encoding="utf-8")
    return None


def _save_to_cache(pdf_path: str, markdown: str) -> None:
    """Saves converted Markdown to disk cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _get_cache_path(pdf_path)
    cache_path.write_text(markdown, encoding="utf-8")
    logger.info(f"Cached parsed output → {cache_path.name}")


def _parse_with_docling(pdf_path: str) -> str | None:
    """
    Converts a PDF to structured Markdown via docling.
    OCR is disabled because ATR PDFs are text-based (not scanned images).
    This avoids needing EasyOCR model files and runs faster.
    Returns Markdown string, or None on failure.
    """
    if not _DOCLING_AVAILABLE:
        return None
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat

        pipeline_opts = PdfPipelineOptions()
        pipeline_opts.do_ocr = False            # ATR PDFs are text-based, not scanned
        pipeline_opts.do_table_structure = True  # Keep table parsing for routing tables

        logger.info(f"docling: converting {Path(pdf_path).name} ...")
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts)
            }
        )
        result = converter.convert(pdf_path)
        markdown = result.document.export_to_markdown()
        return markdown
    except Exception as e:
        logger.error(f"docling conversion failed for {pdf_path}: {e}")
        return None



def _parse_with_pypdf(pdf_path: str) -> str | None:
    """Fallback: raw text extraction via pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        if text.strip():
            logger.info(f"pypdf fallback used for {Path(pdf_path).name}")
            return text
        return None
    except Exception as e:
        logger.error(f"pypdf fallback also failed for {pdf_path}: {e}")
        return None


def extract_structured_text(pdf_path: str, force_refresh: bool = False) -> str:
    """
    Main entry point. Returns the best available structured text for a PDF.

    Priority:
      1. Disk cache (fastest — no ML re-run)
      2. docling conversion (best quality — layout-aware)
      3. pypdf fallback (always available — basic quality)

    Args:
        pdf_path:      Absolute or relative path to the ATR PDF.
        force_refresh: If True, ignore cache and re-run docling.

    Returns:
        Structured text string (Markdown from docling, or raw from pypdf).
        Empty string if all methods fail.
    """
    # 1. Try cache
    if not force_refresh:
        cached = _load_from_cache(pdf_path)
        if cached:
            return cached

    # 2. Try docling
    markdown = _parse_with_docling(pdf_path)
    if markdown:
        _save_to_cache(pdf_path, markdown)
        return markdown

    # 3. Fallback to pypdf
    raw_text = _parse_with_pypdf(pdf_path)
    return raw_text or ""


def extract_links(pdf_path: str) -> list[str]:
    """
    Extracts hyperlink URIs from a PDF using pypdf (docling doesn't surface these).
    Returns a deduplicated list of URLs.
    """
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
                            links.append(uri)
    except Exception as e:
        logger.error(f"Link extraction error for {pdf_path}: {e}")
    return list(set(links))


def trim_to_token_budget(text: str, max_chars: int = 12000) -> str:
    """
    Trims structured text to a character budget while trying to preserve
    whole sections (cuts at the last Markdown heading boundary before the limit).

    For docling Markdown, 12,000 chars ≈ ~3,000 tokens — sufficient for any ATR.
    Original pypdf fallback used a hard 30,000 char limit; this is far more
    efficient because the structured text is already de-noised.

    Args:
        text:      The Markdown / raw text to trim.
        max_chars: Character ceiling (default 12,000).

    Returns:
        Trimmed text, possibly with a truncation notice appended.
    """
    if len(text) <= max_chars:
        return text

    # Try to cut at a clean Markdown section boundary
    truncated = text[:max_chars]
    last_heading = truncated.rfind("\n## ")
    if last_heading == -1:
        last_heading = truncated.rfind("\n# ")

    if last_heading > max_chars * 0.6:  # only cut here if we kept ≥60% of content
        truncated = truncated[:last_heading]

    return truncated + "\n\n...(document truncated for token efficiency)"


def get_parser_info() -> dict:
    """Returns metadata about which parser engine will be used."""
    return {
        "docling_available": _DOCLING_AVAILABLE,
        "cache_dir": str(CACHE_DIR),
        "engine": "docling" if _DOCLING_AVAILABLE else "pypdf (fallback)",
        "max_chars_default": 12000,
    }
