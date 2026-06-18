"""
run_batch_test.py
-----------------
End-to-end batch test: runs docling parsing + Gemini analysis on all PDFs
in output/ and saves results to the database. Prints a summary at the end.
"""

import os
import time
import database
import analyzer

API_KEY = "AIzaSyDgOaf22rgP5jhXR-yUTGmOwZjJrhyrxXs"
FOLDER  = "c:/Work/CPGRAMS/Success Stories/Automation/output"

def main():
    database.init_db()

    files = sorted([f for f in os.listdir(FOLDER) if f.lower().endswith(".pdf")])
    print(f"Starting batch analysis of {len(files)} files...\n")

    results_summary = []
    t_start = time.time()

    for i, filename in enumerate(files):
        filepath = os.path.join(FOLDER, filename)
        t0 = time.time()
        print(f"[{i+1}/{len(files)}] {filename}", end=" ... ", flush=True)

        result = analyzer.analyze_atr(filepath, api_key=API_KEY)
        elapsed = time.time() - t0

        status = result.get("status", "unknown")
        gid    = result.get("grievance_id", "N/A")
        is_ss  = result.get("is_success_story", False)

        if status == "error":
            print(f"ERROR: {result.get('error')} ({elapsed:.1f}s)")
        else:
            database.save_result(filename, result)
            flag = "[SUCCESS STORY]" if is_ss else ""
            print(f"OK  {gid}  {flag}  ({elapsed:.1f}s)")

        results_summary.append({
            "file": filename, "status": status,
            "gid": gid, "success": is_ss, "secs": round(elapsed, 1)
        })

    total = time.time() - t_start
    errors    = [r for r in results_summary if r["status"] == "error"]
    successes = [r for r in results_summary if r["success"]]

    print(f"\n=== BATCH COMPLETE in {total:.0f}s ===")
    print(f"  Analyzed         : {len(results_summary) - len(errors)}/{len(results_summary)}")
    print(f"  Errors           : {len(errors)}")
    print(f"  Success stories  : {len(successes)}")
    for s in successes:
        print(f"    - {s['gid']}")

    if errors:
        print(f"\n  Failed files:")
        for e in errors:
            print(f"    - {e['file']}")

if __name__ == "__main__":
    main()
