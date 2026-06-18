import os
from docling_parser import extract_structured_text, extract_links, trim_to_token_budget

def inspect_pdf(file_path):
    result = f"--- Inspecting: {os.path.basename(file_path)} ---\n"
    try:
        # Links
        links = extract_links(file_path)
        if links:
            result += "[Links/Annotations]\n" + "\n".join(f"  Link -> {u}" for u in links) + "\n"
        else:
            result += "[Links/Annotations]\n  No web links found.\n"

        # Structured text via docling (cached)
        text = extract_structured_text(file_path)
        trimmed = trim_to_token_budget(text, max_chars=12000)
        result += f"\n[Text Stats] Total: {len(text):,} chars | Trimmed to Gemini: {len(trimmed):,} chars\n"
        result += "\n[Text Content Sample]\n" + text[:500] + "...\n"

        # Keywords check
        result += "\n[Keywords Check]\n"
        keywords = ["Forwarded", "Transferred", "Disposed", "Closed", "Action Taken"]
        for k in keywords:
            count = text.lower().count(k.lower())
            result += f"  '{k}': {count} occurrences\n"

    except Exception as e:
        result += f"Error reading PDF: {e}\n"
    
    return result

if __name__ == "__main__":
    folder = "c:/Work/CPGRAMS/Success Stories/Automation/output"
    output_file = "c:/Work/CPGRAMS/Success Stories/Automation/analysis_results.txt"
    
    if os.path.exists(output_file):
        os.remove(output_file)

    results = ""
    if os.path.exists(folder):
        files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
        for f in files:
            results += inspect_pdf(os.path.join(folder, f)) + "\n"
    else:
        results = f"Folder not found: {folder}"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(results)
    
    print(f"Analysis complete. Results saved to {output_file}")
