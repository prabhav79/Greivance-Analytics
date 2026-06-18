import os
import json
import pandas as pd
from sqlalchemy import create_engine, text

# Get DB URL, default to local SQLite if not provided
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///grievance_analysis.db")
# Fix Heroku/Railway postgres:// to postgresql://
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DB_URL)

def init_db():
    is_sqlite = 'sqlite' in DB_URL
    
    # In Postgres, SERIAL implies INTEGER. So for Postgres: id SERIAL PRIMARY KEY
    # For SQLite: id INTEGER PRIMARY KEY AUTOINCREMENT
    pk_stmt = "id INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "id SERIAL PRIMARY KEY"
    
    create_stmt = f'''
        CREATE TABLE IF NOT EXISTS grievances (
            {pk_stmt},
            filename TEXT UNIQUE,
            grievance_id TEXT,
            grievance_type TEXT,
            has_attachment BOOLEAN,
            status TEXT,
            language TEXT,
            is_success_story BOOLEAN,
            success_headline TEXT,
            success_narrative TEXT,
            citizen_problem TEXT,
            resolution_summary TEXT,
            desk_count INTEGER,
            ping_pong_count INTEGER,
            bottleneck_desk TEXT,
            final_resolver TEXT,
            ping_pong_desks TEXT,
            resolved_desk TEXT,
            citizen_feedback TEXT,
            intelligent_issue_summary TEXT,
            intelligent_officer_summary TEXT,
            intelligent_citizen_feedback_summary TEXT,
            attachment_links TEXT,
            raw_json TEXT,
            is_vigilance TEXT,
            vigilance_reasoning TEXT,
            citizen_sentiment TEXT,
            officer_tone TEXT,
            citizen_feedback_sentiment TEXT,
            delay_root_cause TEXT,
            jurisdiction_accuracy TEXT,
            standardized_theme TEXT,
            urgency_score INTEGER,
            is_systemic_issue BOOLEAN,
            policy_recommendation TEXT,
            complainant_name TEXT,
            routing_action TEXT,
            transfer_to_dept TEXT,
            draft_atr_remarks TEXT,
            is_ping_pong_flag BOOLEAN,
            negligence_flag BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    with engine.begin() as conn:
        conn.execute(text(create_stmt))
        
def save_result(filename, data):
    with engine.begin() as conn:
        res = conn.execute(text("SELECT id FROM grievances WHERE filename = :f"), {"f": filename}).fetchone()
        
        if res:
            stmt = text('''
                UPDATE grievances SET
                    grievance_id=:gid, grievance_type=:gtype, has_attachment=:hatt, status=:status, language=:lang, is_success_story=:iss, 
                    success_headline=:sh, success_narrative=:sn, citizen_problem=:cp, resolution_summary=:rs,
                    desk_count=:dc, ping_pong_count=:ppc, bottleneck_desk=:bd, final_resolver=:fr,
                    ping_pong_desks=:ppd, resolved_desk=:rd, citizen_feedback=:cf,
                    intelligent_issue_summary=:iis, intelligent_officer_summary=:ios, intelligent_citizen_feedback_summary=:icfs,
                    citizen_sentiment=:cs, officer_tone=:ot, citizen_feedback_sentiment=:cfs,
                    delay_root_cause=:drc, jurisdiction_accuracy=:ja, standardized_theme=:st,
                    urgency_score=:us, is_systemic_issue=:isi, policy_recommendation=:pr,
                    attachment_links=:al, raw_json=:rj, created_at=CURRENT_TIMESTAMP
                WHERE filename=:fname
            ''')
        else:
            stmt = text('''
                INSERT INTO grievances (
                    filename, grievance_id, grievance_type, has_attachment, status, language, is_success_story, 
                    success_headline, success_narrative, citizen_problem, resolution_summary,
                    desk_count, ping_pong_count, bottleneck_desk, final_resolver,
                    ping_pong_desks, resolved_desk, citizen_feedback,
                    intelligent_issue_summary, intelligent_officer_summary, intelligent_citizen_feedback_summary,
                    citizen_sentiment, officer_tone, citizen_feedback_sentiment,
                    delay_root_cause, jurisdiction_accuracy, standardized_theme,
                    urgency_score, is_systemic_issue, policy_recommendation,
                    attachment_links, raw_json
                ) VALUES (
                    :fname, :gid, :gtype, :hatt, :status, :lang, :iss,
                    :sh, :sn, :cp, :rs,
                    :dc, :ppc, :bd, :fr,
                    :ppd, :rd, :cf,
                    :iis, :ios, :icfs,
                    :cs, :ot, :cfs,
                    :drc, :ja, :st,
                    :us, :isi, :pr,
                    :al, :rj
                )
            ''')
            
        params = {
            "fname": filename,
            "gid": data.get('grievance_id'), "gtype": data.get('grievance_type'), "hatt": data.get('has_attachment'),
            "status": data.get('status'), "lang": data.get('language'), "iss": data.get('is_success_story'),
            "sh": data.get('success_headline'), "sn": data.get('success_narrative'), "cp": data.get('citizen_problem'), "rs": data.get('resolution_summary'),
            "dc": data.get('desk_count'), "ppc": data.get('ping_pong_count'), "bd": data.get('bottleneck_desk'), "fr": data.get('final_resolver'),
            "ppd": json.dumps(data.get('ping_pong_desks', [])), "rd": data.get('resolved_desk'), "cf": data.get('citizen_feedback'),
            "iis": data.get('intelligent_issue_summary'), "ios": data.get('intelligent_officer_summary'), "icfs": data.get('intelligent_citizen_feedback_summary'),
            "cs": data.get('citizen_sentiment'), "ot": data.get('officer_tone'), "cfs": data.get('citizen_feedback_sentiment'),
            "drc": data.get('delay_root_cause'), "ja": data.get('jurisdiction_accuracy'), "st": data.get('standardized_theme'),
            "us": data.get('urgency_score'), "isi": data.get('is_systemic_issue'), "pr": data.get('policy_recommendation'),
            "al": json.dumps(data.get('attachment_links', [])), "rj": json.dumps(data)
        }
        conn.execute(stmt, params)

def save_vigilance_result(filename, data):
    with engine.begin() as conn:
        res = conn.execute(text("SELECT id FROM grievances WHERE filename = :f"), {"f": filename}).fetchone()
        if res:
            stmt = text('''
                UPDATE grievances SET
                    grievance_id=COALESCE(:gid, grievance_id), 
                    is_vigilance=:iv, 
                    vigilance_reasoning=:vr
                WHERE filename=:fname
            ''')
        else:
            stmt = text('''
                INSERT INTO grievances (
                    filename, grievance_id, is_vigilance, vigilance_reasoning, status
                ) VALUES (:fname, :gid, :iv, :vr, 'analyzed')
            ''')
            
        conn.execute(stmt, {
            "fname": filename, "gid": data.get('grievance_id'), 
            "iv": data.get('is_vigilance'), "vr": data.get('vigilance_reasoning')
        })

def save_routing_result(filename, data):
    with engine.begin() as conn:
        res = conn.execute(text("SELECT id FROM grievances WHERE filename = :f"), {"f": filename}).fetchone()
        if res:
            stmt = text('''
                UPDATE grievances SET
                    grievance_id=COALESCE(:gid, grievance_id),
                    complainant_name=:cn,
                    routing_action=:ra,
                    transfer_to_dept=:ttd,
                    draft_atr_remarks=:dar,
                    is_ping_pong_flag=:ippf,
                    negligence_flag=:nf,
                    desk_count=COALESCE(:dc, desk_count),
                    ping_pong_count=COALESCE(:ppc, ping_pong_count),
                    delay_root_cause=COALESCE(:drc, delay_root_cause),
                    standardized_theme=COALESCE(:st, standardized_theme),
                    urgency_score=COALESCE(:us, urgency_score)
                WHERE filename=:fname
            ''')
        else:
            stmt = text('''
                INSERT INTO grievances (
                    filename, grievance_id, complainant_name, routing_action, transfer_to_dept,
                    draft_atr_remarks, is_ping_pong_flag, negligence_flag,
                    desk_count, ping_pong_count, delay_root_cause, standardized_theme, urgency_score,
                    status
                ) VALUES (:fname, :gid, :cn, :ra, :ttd, :dar, :ippf, :nf, :dc, :ppc, :drc, :st, :us, 'analyzed')
            ''')
        
        conn.execute(stmt, {
            "fname": filename, "gid": data.get('grievance_id'), "cn": data.get('complainant_name'), 
            "ra": data.get('routing_action'), "ttd": data.get('transfer_to_dept'), "dar": data.get('draft_atr_remarks'), 
            "ippf": data.get('is_ping_pong_flag'), "nf": data.get('negligence_flag'), 
            "dc": data.get('desk_count'), "ppc": data.get('ping_pong_count'), 
            "drc": data.get('delay_root_cause'), "st": data.get('standardized_theme'), "us": data.get('urgency_score')
        })

def get_all_results():
    with engine.connect() as conn:
        results = pd.read_sql_query("SELECT * FROM grievances", conn)
    return results

def clear_db():
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM grievances"))
        print("Database cleared.")

if __name__ == "__main__":
    init_db()
