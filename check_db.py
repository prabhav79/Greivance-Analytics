import sqlite3
import pandas as pd
import os

db_path = "c:/Work/CPGRAMS/Success Stories/Automation/grievance_analysis.db"
csv_path = "c:/Work/CPGRAMS/Success Stories/Automation/2025-12-14T10-05_export.csv"

print(f"--- Checking DB: {db_path} ---")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM grievances", conn)
        print(f"Row Count: {len(df)}")
        if not df.empty:
            print("\nSAMPLE DATA:")
            print(df[['filename', 'status', 'grievance_id']].head())
            print("\nSTATUS COUNTS:")
            print(df['status'].value_counts())
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()
else:
    print("DB File not found.")

print(f"\n--- Checking CSV: {csv_path} ---")
if os.path.exists(csv_path):
    with open(csv_path, 'r') as f:
        print(f.read())
else:
    print("CSV File not found.")
