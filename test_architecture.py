import json
import os
from analyzer import analyze_atr

# Test with Groq
api_key_groq = os.getenv("GROQ_API_KEY", "")
# Test with Gemini
api_key_gemini = os.getenv("GEMINI_API_KEY", "")

pdf_path = r"c:\Work\CPGRAMS\Success Stories\Automation\output\PMOPG_E_2025_0091753.pdf"

if os.path.exists(pdf_path):
    print("PDF exists. Testing pypdf extraction...")
    from pdf_extractor import extract_raw_text
    print(extract_raw_text(pdf_path)[:100])
else:
    print("PDF not found for testing.")
