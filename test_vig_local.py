import os
import json
from analyzer import analyze_vigilance

API_KEY = "AIzaSyDgOaf22rgP5jhXR-yUTGmOwZjJrhyrxXs"
PDF_PATH = r"c:\Work\CPGRAMS\Success Stories\Automation\output\PRSEC_E_2025_0062377.pdf"

if __name__ == "__main__":
    if not os.path.exists(PDF_PATH):
        print("PDF not found!")
    else:
        print(f"Analyzing {os.path.basename(PDF_PATH)} for vigilance angle...")
        result = analyze_vigilance(PDF_PATH, API_KEY)
        print("--- Result ---")
        print(json.dumps(result, indent=2))
