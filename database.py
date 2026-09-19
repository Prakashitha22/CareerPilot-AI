import os
import sqlite3
import json
from datetime import datetime

# Default database file path in project root
DB_FILENAME = "careerpilot.db"
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)

def get_db_path(db_path=None):
    """Return configured database path or default."""
    return db_path or DEFAULT_DB_PATH

def get_db_connection(db_path=None):
    """
    Establish a connection to the SQLite database.
    Configures row_factory to sqlite3.Row for dictionary-like column access.
    Enables foreign keys support.
    """
    path = get_db_path(db_path)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=None):
    """
    Initialize SQLite database and create required relational tables and indexes.
    Safe to call repeatedly (uses CREATE TABLE IF NOT EXISTS).
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            # 1. Candidates Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_name TEXT NOT NULL DEFAULT 'Candidate',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Resume Analyses Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resume_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    resume_filename TEXT DEFAULT 'resume.pdf',
                    summary TEXT,
                    education TEXT,
                    technical_skills TEXT,
                    soft_skills TEXT,
                    experience TEXT,
                    projects TEXT,
                    certifications TEXT,
                    strengths TEXT,
                    missing_skills TEXT,
                    suggested_roles TEXT,
                    resume_improvements TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
                );
            """)

            # 3. Interview Sessions Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interview_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    target_role TEXT NOT NULL,
                    questions TEXT,
                    answers TEXT,
                    evaluations TEXT,
                    overall_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
                );
            """)

            # 4. Career Reports Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS career_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    target_role TEXT NOT NULL,
                    readiness_percentage INTEGER DEFAULT 0,
                    skill_gap TEXT,
                    role_matching TEXT,
                    learning_roadmap TEXT,
                    recommended_projects TEXT,
                    resume_checklist TEXT,
                    career_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
                );
            """)

            # Performance Indexes for Fast Lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_resume_candidate ON resume_analyses(candidate_id, created_at DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_interview_candidate ON interview_sessions(candidate_id, created_at DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_career_candidate ON career_reports(candidate_id, created_at DESC);")
    finally:
        conn.close()

# ==========================================
# CANDIDATE OPERATIONS
# ==========================================

def create_candidate(candidate_name="Candidate", db_path=None):
    """Create a new candidate record and return its integer ID."""
    clean_name = str(candidate_name or "Candidate").strip() or "Candidate"
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO candidates (candidate_name, created_at, updated_at) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);",
                (clean_name,)
            )
            return cursor.lastrowid
    finally:
        conn.close()

def get_candidate(candidate_id, db_path=None):
    """Retrieve candidate dictionary by ID, or None if not found."""
    if not candidate_id:
        return None
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute("SELECT * FROM candidates WHERE id = ?;", (candidate_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def update_candidate_name(candidate_id, candidate_name, db_path=None):
    """Update candidate's name when extracted from resume analysis."""
    if not candidate_id or not candidate_name:
        return False
    clean_name = str(candidate_name).strip()
    if not clean_name or clean_name.lower() == 'candidate':
        return False
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute(
                "UPDATE candidates SET candidate_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (clean_name, candidate_id)
            )
            return True
    finally:
        conn.close()

# ==========================================
# RESUME ANALYSIS OPERATIONS
# ==========================================

def save_resume_analysis(candidate_id, resume_filename, analysis_data, db_path=None):
    """
    Save resume analysis results safely into SQLite.
    Serializes list and dictionary fields as JSON strings.
    """
    if not candidate_id or not isinstance(analysis_data, dict):
        return None

    filename = str(resume_filename or 'resume.pdf').strip()
    summary = str(analysis_data.get('summary') or '').strip()
    
    edu_json = json.dumps(analysis_data.get('education') or [])
    tech_json = json.dumps(analysis_data.get('technical_skills') or [])
    soft_json = json.dumps(analysis_data.get('soft_skills') or [])
    exp_json = json.dumps(analysis_data.get('experience') or [])
    proj_json = json.dumps(analysis_data.get('projects') or [])
    cert_json = json.dumps(analysis_data.get('certifications') or [])
    strengths_json = json.dumps(analysis_data.get('strengths') or [])
    missing_json = json.dumps(analysis_data.get('missing_skills') or [])
    roles_json = json.dumps(analysis_data.get('suggested_roles') or [])
    improve_json = json.dumps(analysis_data.get('resume_improvements') or [])

    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute("""
                INSERT INTO resume_analyses (
                    candidate_id, resume_filename, summary, education,
                    technical_skills, soft_skills, experience, projects,
                    certifications, strengths, missing_skills,
                    suggested_roles, resume_improvements, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, (
                candidate_id, filename, summary, edu_json,
                tech_json, soft_json, exp_json, proj_json,
                cert_json, strengths_json, missing_json,
                roles_json, improve_json
            ))
            return cursor.lastrowid
    finally:
        conn.close()

def get_latest_resume_analysis(candidate_id, db_path=None):
    """Retrieve the most recent resume analysis for a candidate."""
    if not candidate_id:
        return None
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            "SELECT * FROM resume_analyses WHERE candidate_id = ? ORDER BY created_at DESC, id DESC LIMIT 1;",
            (candidate_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return _deserialize_resume_analysis(dict(row))
    finally:
        conn.close()

# ==========================================
# INTERVIEW SESSION OPERATIONS
# ==========================================

def save_interview_session(candidate_id, target_role, questions, answers, evaluations, overall_score, db_path=None):
    """
    Save an interview session with Q&A history and score.
    """
    if not candidate_id:
        return None

    role = str(target_role or 'Software Engineer').strip()
    q_json = json.dumps(questions or [])
    a_json = json.dumps(answers or [])
    e_json = json.dumps(evaluations or [])
    score = round(float(overall_score or 0.0), 1)

    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute("""
                INSERT INTO interview_sessions (
                    candidate_id, target_role, questions, answers, evaluations, overall_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, (candidate_id, role, q_json, a_json, e_json, score))
            return cursor.lastrowid
    finally:
        conn.close()

def get_latest_interview_session(candidate_id, db_path=None):
    """Retrieve the most recent interview session for a candidate."""
    if not candidate_id:
        return None
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            "SELECT * FROM interview_sessions WHERE candidate_id = ? ORDER BY created_at DESC, id DESC LIMIT 1;",
            (candidate_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return _deserialize_interview_session(dict(row))
    finally:
        conn.close()

# ==========================================
# CAREER REPORT OPERATIONS
# ==========================================

def save_career_report(candidate_id, target_role, report_data, db_path=None):
    """
    Save a career intelligence report safely into SQLite.
    """
    if not candidate_id or not isinstance(report_data, dict):
        return None

    role = str(target_role or report_data.get('role') or 'Python Developer').strip()
    readiness = int(report_data.get('readiness', {}).get('percentage', 70) if isinstance(report_data.get('readiness'), dict) else 70)
    
    gap_json = json.dumps(report_data.get('skill_gap') or {})
    match_json = json.dumps(report_data.get('role_matching') or [])
    map_json = json.dumps(report_data.get('learning_roadmap') or [])
    proj_json = json.dumps(report_data.get('recommended_projects') or [])
    check_json = json.dumps(report_data.get('resume_checklist') or [])
    summary_json = json.dumps(report_data.get('career_summary') or {})

    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute("""
                INSERT INTO career_reports (
                    candidate_id, target_role, readiness_percentage, skill_gap,
                    role_matching, learning_roadmap, recommended_projects,
                    resume_checklist, career_summary, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, (
                candidate_id, role, readiness, gap_json,
                match_json, map_json, proj_json,
                check_json, summary_json
            ))
            return cursor.lastrowid
    finally:
        conn.close()

def get_latest_career_report(candidate_id, db_path=None):
    """Retrieve the most recent career intelligence report for a candidate."""
    if not candidate_id:
        return None
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            "SELECT * FROM career_reports WHERE candidate_id = ? ORDER BY created_at DESC, id DESC LIMIT 1;",
            (candidate_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return _deserialize_career_report(dict(row))
    finally:
        conn.close()

# ==========================================
# CAREER HISTORY AGGREGATION & VIEW
# ==========================================

def get_candidate_history(candidate_id, db_path=None):
    """
    Returns an aggregated, unified list of all candidate activities
    (resume scans, mock interviews, and career reports) sorted by most recent first.
    """
    if not candidate_id:
        return []

    conn = get_db_connection(db_path)
    history = []
    try:
        # 1. Resume Analyses
        cur = conn.execute("""
            SELECT id, resume_filename, summary, technical_skills, created_at
            FROM resume_analyses
            WHERE candidate_id = ?
            ORDER BY created_at DESC;
        """, (candidate_id,))
        for r in cur.fetchall():
            tech = _safe_json_loads(r['technical_skills'], [])
            history.append({
                'id': r['id'],
                'record_type': 'resume_analysis',
                'type_label': 'Resume Analysis',
                'icon': '📄',
                'title': f"Resume Scan: {r['resume_filename']}",
                'subtitle': f"{len(tech)} Technical Skills Identified",
                'badge': f"{len(tech)} Skills",
                'badge_class': 'badge-history-resume',
                'created_at': r['created_at'],
                'date_formatted': _format_timestamp(r['created_at'])
            })

        # 2. Interview Sessions
        cur = conn.execute("""
            SELECT id, target_role, overall_score, questions, created_at
            FROM interview_sessions
            WHERE candidate_id = ?
            ORDER BY created_at DESC;
        """, (candidate_id,))
        for r in cur.fetchall():
            qs = _safe_json_loads(r['questions'], [])
            q_count = len(qs) if qs else 5
            score = round(float(r['overall_score'] or 0.0), 1)
            history.append({
                'id': r['id'],
                'record_type': 'interview_session',
                'type_label': 'Interview Session',
                'icon': '🎯',
                'title': f"Mock Interview: {r['target_role']}",
                'subtitle': f"{q_count} Questions Completed",
                'badge': f"{score}/10 Score",
                'badge_class': 'badge-history-interview',
                'created_at': r['created_at'],
                'date_formatted': _format_timestamp(r['created_at'])
            })

        # 3. Career Reports
        cur = conn.execute("""
            SELECT id, target_role, readiness_percentage, created_at
            FROM career_reports
            WHERE candidate_id = ?
            ORDER BY created_at DESC;
        """, (candidate_id,))
        for r in cur.fetchall():
            pct = int(r['readiness_percentage'] or 0)
            history.append({
                'id': r['id'],
                'record_type': 'career_report',
                'type_label': 'Career Intelligence',
                'icon': '📈',
                'title': f"Career Intelligence: {r['target_role']}",
                'subtitle': f"{pct}% Readiness Calibrated",
                'badge': f"{pct}% Ready",
                'badge_class': 'badge-history-career',
                'created_at': r['created_at'],
                'date_formatted': _format_timestamp(r['created_at'])
            })

        # Sort combined history by created_at descending
        history.sort(key=lambda x: x['created_at'] or '', reverse=True)
        return history
    finally:
        conn.close()

def get_record_detail(record_type, record_id, candidate_id=None, db_path=None):
    """
    Fetch a specific history record and deserialize all JSON fields into clean Python structures.
    Ensures users view human-readable information with zero exposed raw JSON.
    """
    conn = get_db_connection(db_path)
    try:
        if record_type == 'resume_analysis':
            query = "SELECT * FROM resume_analyses WHERE id = ?"
            params = [record_id]
            if candidate_id:
                query += " AND candidate_id = ?"
                params.append(candidate_id)
            row = conn.execute(query, params).fetchone()
            return _deserialize_resume_analysis(dict(row)) if row else None

        elif record_type == 'interview_session':
            query = "SELECT * FROM interview_sessions WHERE id = ?"
            params = [record_id]
            if candidate_id:
                query += " AND candidate_id = ?"
                params.append(candidate_id)
            row = conn.execute(query, params).fetchone()
            return _deserialize_interview_session(dict(row)) if row else None

        elif record_type == 'career_report':
            query = "SELECT * FROM career_reports WHERE id = ?"
            params = [record_id]
            if candidate_id:
                query += " AND candidate_id = ?"
                params.append(candidate_id)
            row = conn.execute(query, params).fetchone()
            return _deserialize_career_report(dict(row)) if row else None

        return None
    finally:
        conn.close()

def clear_candidate_history(candidate_id, db_path=None):
    """
    Safely delete all career records for the given candidate ID.
    Does NOT delete other candidates or drop database tables.
    """
    if not candidate_id:
        return False
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute("DELETE FROM resume_analyses WHERE candidate_id = ?;", (candidate_id,))
            conn.execute("DELETE FROM interview_sessions WHERE candidate_id = ?;", (candidate_id,))
            conn.execute("DELETE FROM career_reports WHERE candidate_id = ?;", (candidate_id,))
            return True
    finally:
        conn.close()

# ==========================================
# INTERNAL DESERIALIZATION HELPERS
# ==========================================

def _safe_json_loads(val, default):
    if not val:
        return default
    try:
        return json.loads(val)
    except (ValueError, TypeError):
        return default

def _format_timestamp(ts):
    if not ts:
        return "Recent"
    try:
        # SQLite CURRENT_TIMESTAMP is UTC format: YYYY-MM-DD HH:MM:SS
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except Exception:
        return str(ts)

def _deserialize_resume_analysis(row):
    return {
        'id': row['id'],
        'candidate_id': row['candidate_id'],
        'resume_filename': row.get('resume_filename', 'resume.pdf'),
        'summary': row.get('summary', ''),
        'education': _safe_json_loads(row.get('education'), []),
        'technical_skills': _safe_json_loads(row.get('technical_skills'), []),
        'soft_skills': _safe_json_loads(row.get('soft_skills'), []),
        'experience': _safe_json_loads(row.get('experience'), []),
        'projects': _safe_json_loads(row.get('projects'), []),
        'certifications': _safe_json_loads(row.get('certifications'), []),
        'strengths': _safe_json_loads(row.get('strengths'), []),
        'missing_skills': _safe_json_loads(row.get('missing_skills'), []),
        'suggested_roles': _safe_json_loads(row.get('suggested_roles'), []),
        'resume_improvements': _safe_json_loads(row.get('resume_improvements'), []),
        'created_at': row.get('created_at'),
        'date_formatted': _format_timestamp(row.get('created_at')),
        'record_type': 'resume_analysis'
    }

def _deserialize_interview_session(row):
    return {
        'id': row['id'],
        'candidate_id': row['candidate_id'],
        'target_role': row.get('target_role', 'Software Engineer'),
        'questions': _safe_json_loads(row.get('questions'), []),
        'answers': _safe_json_loads(row.get('answers'), []),
        'evaluations': _safe_json_loads(row.get('evaluations'), []),
        'overall_score': round(float(row.get('overall_score') or 0.0), 1),
        'created_at': row.get('created_at'),
        'date_formatted': _format_timestamp(row.get('created_at')),
        'record_type': 'interview_session'
    }

def _deserialize_career_report(row):
    return {
        'id': row['id'],
        'candidate_id': row['candidate_id'],
        'target_role': row.get('target_role', 'Python Developer'),
        'readiness_percentage': int(row.get('readiness_percentage') or 0),
        'skill_gap': _safe_json_loads(row.get('skill_gap'), {}),
        'role_matching': _safe_json_loads(row.get('role_matching'), []),
        'learning_roadmap': _safe_json_loads(row.get('learning_roadmap'), []),
        'recommended_projects': _safe_json_loads(row.get('recommended_projects'), []),
        'resume_checklist': _safe_json_loads(row.get('resume_checklist'), []),
        'career_summary': _safe_json_loads(row.get('career_summary'), {}),
        'created_at': row.get('created_at'),
        'date_formatted': _format_timestamp(row.get('created_at')),
        'record_type': 'career_report'
    }
