import os
import analyzer
import database

# API Key from dashboard
api_key = "AIzaSyDgOaf22rgP5jhXR-yUTGmOwZjJrhyrxXs"
test_file = "c:/Work/CPGRAMS/Success Stories/Automation/output/PRSEC_E_2024_0042116.pdf"

print("Initializing DB...")
database.init_db()

print(f"Analyzing {os.path.basename(test_file)}...")
result = analyzer.analyze_atr(test_file, api_key=api_key)

if 'error' in result:
    print("Error during analysis:", result['error'])
else:
    keys_to_verify = [
        'intelligent_issue_summary', 'intelligent_officer_summary', 'intelligent_citizen_feedback_summary',
        'citizen_sentiment', 'officer_tone', 'citizen_feedback_sentiment',
        'delay_root_cause', 'jurisdiction_accuracy', 'standardized_theme',
        'urgency_score', 'is_systemic_issue', 'policy_recommendation'
    ]

    print("Analysis success. Keys parsed:")
    for key in keys_to_verify:
        val = result.get(key, 'MISSING')
        val_str = str(val)[:100] + "..." if isinstance(val, str) else str(val)
        print(f" - {key}: {val_str}")
        
    print("\nSaving to Database...")
    database.save_result(os.path.basename(test_file), result)
    print("Saved.")
    
    # Verify in DB
    df = database.get_all_results()
    row = df[df['filename'] == os.path.basename(test_file)].iloc[0]
    print("\nDB Verification:")
    for key in keys_to_verify:
        print(f" - {key}: {row.get(key, 'MISSING')}")
        
    print("\nDONE!")
