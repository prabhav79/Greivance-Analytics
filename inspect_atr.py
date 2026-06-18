
import os
from docling_parser import extract_structured_text, extract_links, trim_to_token_budget

def inspect_pdf(file_path):
    print(f"--- Inspecting: {os.path.basename(file_path)} ---")
    try:
        # Links (still extracted via pypdf annotations internally)
        print("[Links/Annotations]")
        links = extract_links(file_path)
        if links:
            for uri in links:
                print(f"  Found Link -> {uri}")
        else:
            print("  No web links found.")

        # Structured text via docling (or pypdf fallback)
        print("\n[Structured Text Sample — via docling_parser]")
        text = extract_structured_text(file_path)
        trimmed = trim_to_token_budget(text, max_chars=12000)
        print(f"  Total chars: {len(text):,}  |  Trimmed (sent to Gemini): {len(trimmed):,}")
        print()
        print(text[:1500])

        # Keywords check
        print("\n[Keywords Check]")
        keywords = ["Forwarded", "Transferred", "Disposed", "Closed", "Action Taken"]
        for k in keywords:
            count = text.lower().count(k.lower())
            print(f"  '{k}': {count} occurrences")

    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    folder = "c:/Work/CPGRAMS/Success Stories/Automation/output"
    files = [
        "MONRE_E_2024_0000217.pdf",
        "PMOPG_E_2024_0094406.pdf"
    ]
    
    for f in files:
        path = os.path.join(folder, f)
        if os.path.exists(path):
            inspect_pdf(path)
        else:
            print(f"File not found: {path}")
