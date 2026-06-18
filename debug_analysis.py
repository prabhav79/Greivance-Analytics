import os
import analyzer
import json
from docling_parser import extract_structured_text, trim_to_token_budget

def test_single_file():
    folder_path = "c:/Work/CPGRAMS/Success Stories/Automation/output"
    files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    
    if not files:
        print("No PDFs found!")
        return

    # Pick user specific file if possible or just the first one
    test_file = files[0] # Just pick one
    filepath = os.path.join(folder_path, test_file)
    
    print(f"--- Debugging: {test_file} ---")
    
    # 1. Test Text Extraction (via docling_parser)
    print("Extracting structured text (docling)...")
    text = extract_structured_text(filepath)
    trimmed = trim_to_token_budget(text, max_chars=12000)
    print(f"Text Length: {len(text):,} raw chars | {len(trimmed):,} after 12k trim (sent to Gemini)")
    
    # 2. Test LLM Call
    print("\nCalling LLM (Gemini)...")
    api_key = "AIzaSyDgOaf22rgP5jhXR-yUTGmOwZjJrhyrxXs"
    result = analyzer.analyze_atr(filepath, api_key=api_key)
    
    print("\n--- LLM Result ---")
    print(json.dumps(result, indent=2))
    
    if result.get('status') == 'error':
        print("\n❌ ANALYSIS FAILED")
    else:
        print("\n✅ ANALYSIS SUCCESS")

if __name__ == "__main__":
    test_single_file()
