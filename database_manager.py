import sqlite3
import json
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Grievance:
    registration_number: str
    name: Optional[str] = None
    date_of_receipt: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None # Closed, Disposed, etc.
    action_taken: Optional[str] = None
    full_text: Optional[str] = None
    pdf_filename: Optional[str] = None

class DatabaseManager:
    def __init__(self, db_path="grievances.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grievances (
                registration_number TEXT PRIMARY KEY,
                name TEXT,
                date_of_receipt TEXT,
                district TEXT,
                state TEXT,
                mobile TEXT,
                email TEXT,
                description TEXT,
                status TEXT,
                action_taken TEXT,
                full_text TEXT,
                pdf_filename TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def insert_grievance(self, grievance: Grievance):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        data = asdict(grievance)
        
        # Upsert logic (replace if exists)
        placeholders = ", ".join(["?"] * len(data))
        keys = ", ".join(data.keys())
        # Using REPLACE INTO to handle updates via primary key conflict
        cursor.execute(f'''
            REPLACE INTO grievances ({keys}) VALUES ({placeholders})
        ''', list(data.values()))
        
        conn.commit()
        conn.close()

    def get_all_grievances(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM grievances")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_grievance(self, reg_num):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM grievances WHERE registration_number = ?", (reg_num,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
