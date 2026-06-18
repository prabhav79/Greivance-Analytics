"""
test_docling.py
---------------
Validates the docling parser on a sample ATR PDF and reports:
  - Whether docling or pypdf was used (parser engine)
  - Character count before vs. after (token savings)
  - A preview of the structured Markdown output
  - Cache path where the result is saved

Run from the Automation directory:
    python test_docling.py
or specify a specific PDF:
    python test_docling.py DEABD_E_2024_0017822.pdf
"""

import sys
import os
import time
from pathlib import Path

# ── Setup ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"

def pick_pdf(arg=None) -> Path:
    """Returns the PDF path to test against."""
    if arg:
        candidate = OUTPUT_DIR / arg
        if candidate.exists():
            return candidate
        # Try as absolute
        if Path(arg).exists():
            return Path(arg)
        print(f"[!] File not found: {arg}")
        sys.exit(1)
    # Default: first PDF in output/
    pdfs = sorted(OUTPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print("[!] No PDFs found in output/. Add some ATR PDFs and try again.")
        sys.exit(1)
    return pdfs[0]


def separator(title=""):
    width = 70
    if title:
        print(f"\n{'-'*10} {title} {'-'*(width - len(title) - 12)}")
    else:
        print("-" * width)


def main():
    pdf_path = pick_pdf(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"\n[TEST] Testing docling parser on: {pdf_path.name}")

    # -- Import parser info ----------------------------------------------------
    from docling_parser import extract_structured_text, trim_to_token_budget, get_parser_info

    info = get_parser_info()
    separator("Parser Configuration")
    print(f"  Engine     : {info['engine']}")
    print(f"  Cache dir  : {info['cache_dir']}")
    print(f"  Max chars  : {info['max_chars_default']:,}")

    # -- Run pypdf for baseline ------------------------------------------------
    separator("Baseline -- pypdf (old method)")
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        pypdf_text = "".join(page.extract_text() or "" for page in reader.pages)
        print(f"  Raw chars extracted : {len(pypdf_text):,}")
        print(f"  After 30k hard cap  : {min(len(pypdf_text), 30000):,}")
        print(f"\n  First 300 chars of pypdf output:")
        print(f"  {repr(pypdf_text[:300])}")
    except Exception as e:
        print(f"  pypdf failed: {e}")
        pypdf_text = ""

    # -- Run docling -----------------------------------------------------------
    separator("docling structured output (new method)")
    t0 = time.time()
    structured_text = extract_structured_text(str(pdf_path), force_refresh=False)
    elapsed = time.time() - t0

    trimmed_text = trim_to_token_budget(structured_text, max_chars=12000)

    print(f"  Extraction time     : {elapsed:.2f}s")
    print(f"  Raw chars (docling) : {len(structured_text):,}")
    print(f"  After 12k trim      : {len(trimmed_text):,}")

    if len(pypdf_text) > 0:
        savings = (1 - len(trimmed_text) / min(len(pypdf_text), 30000)) * 100
        print(f"  Token reduction     : ~{savings:.0f}% fewer chars vs. old method")

    separator("Structured Markdown Preview (first 1500 chars)")
    preview = structured_text[:1500].encode("ascii", errors="backslashreplace").decode("ascii")
    print(preview)

    separator("Trimmed version sent to Gemini (first 500 chars)")
    preview2 = trimmed_text[:500].encode("ascii", errors="backslashreplace").decode("ascii")
    print(preview2)

    # -- Cache check -----------------------------------------------------------
    separator("Cache")
    cache_path = SCRIPT_DIR / "output" / "parsed_cache" / f"{pdf_path.stem}.md"
    if cache_path.exists():
        print(f"  [OK] Cache file exists: {cache_path}")
        print(f"       Size: {cache_path.stat().st_size:,} bytes")
        print(f"       Next run will use cache (0s ML overhead).")
    else:
        print(f"  [!]  Cache file not found at expected path: {cache_path}")

    separator()
    print("[DONE] Test complete.\n")


if __name__ == "__main__":
    main()
