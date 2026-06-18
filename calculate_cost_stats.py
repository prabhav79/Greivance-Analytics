import os
import statistics
from docling_parser import extract_structured_text, trim_to_token_budget

OUTPUT_DIR = "c:/Work/CPGRAMS/Success Stories/Automation/output"
PROMPT_OVERHEAD_CHARS = 1600  # Approx prompt intro + instructions
TOKEN_BUDGET = 12000           # New trimmed ceiling (was 30000)

def calculate_stats():
    print("--- Cost Stats: docling pipeline ---")
    files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith(".pdf")]

    raw_counts = []
    trimmed_counts = []

    for f in files:
        path = os.path.join(OUTPUT_DIR, f)
        text = extract_structured_text(path)   # uses cache if available
        if text:
            raw_counts.append(len(text))
            trimmed_counts.append(len(trim_to_token_budget(text, max_chars=TOKEN_BUDGET)))

    if not raw_counts:
        print("No files found.")
        return

    avg_raw    = statistics.mean(raw_counts)
    avg_trim   = statistics.mean(trimmed_counts)
    max_raw    = max(raw_counts)
    max_trim   = max(trimmed_counts)

    # Estimate tokens (1 token ~= 4 chars)
    avg_input_tokens_old = (min(avg_raw, 30000) + PROMPT_OVERHEAD_CHARS) / 4
    avg_input_tokens_new = (avg_trim + PROMPT_OVERHEAD_CHARS) / 4
    savings_pct = (1 - avg_input_tokens_new / avg_input_tokens_old) * 100

    print(f"Files: {len(raw_counts)}")
    print(f"")
    print(f"  Old pipeline (pypdf, 30k cap):")
    print(f"    Avg chars sent   : {min(avg_raw, 30000):,.0f}")
    print(f"    Avg input tokens : ~{avg_input_tokens_old:,.0f}")
    print(f"")
    print(f"  New pipeline (docling, 12k trim):")
    print(f"    Avg chars sent   : {avg_trim:,.0f}")
    print(f"    Max chars sent   : {max_trim:,}")
    print(f"    Avg input tokens : ~{avg_input_tokens_new:,.0f}")
    print(f"")
    print(f"  Token reduction  : ~{savings_pct:.0f}% fewer input tokens per file")
    
if __name__ == "__main__":
    calculate_stats()
