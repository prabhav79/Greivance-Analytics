import database

print("Initializing DB...")
database.init_db()

print("Testing save...")
database.save_result("test_dummy_file.pdf", {
    "grievance_id": "TEST_ID_123",
    "status": "analyzed",
    "language": "english",
    "is_success_story": False,
    "success_headline": "Test",
    "success_narrative": "Test narrative",
    "citizen_problem": "Test problem",
    "resolution_summary": "Test resolution",
    "desk_count": 0,
    "ping_pong_count": 0,
    "bottleneck_desk": "Test",
    "final_resolver": "Test Resolver",
    "ping_pong_desks": [],
    "resolved_desk": "Test Desk",
    "citizen_feedback": "Test Feedback",
    "intelligent_issue_summary": "Summary 1",
    "intelligent_officer_summary": "Summary 2",
    "intelligent_citizen_feedback_summary": "Summary 3",
    "attachment_links": []
})
print("Save executed. Checking DB...")
df = database.get_all_results()
print("Total rows:", len(df))
if len(df[df['filename'] == "test_dummy_file.pdf"]) > 0:
    print("SUCCESS: Test row inserted successfully!")
else:
    print("ERROR: Row not found.")
