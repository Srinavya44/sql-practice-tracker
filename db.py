# db.py - database helpers for SQL Practice Playground
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime

DB_PATH = Path(__file__).parent / "practice.db"

def get_conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)

def run_sql_file(conn, path):
    sql = Path(path).read_text(encoding="utf-8")
    conn.executescript(sql)

def init_db(schema_path=None, seed_path=None):
    """Create schema and seed data if needed. Accepts optional paths relative to project root."""
    schema_path = schema_path or (Path(__file__).parent / "sql" / "schema.sql")
    seed_path = seed_path or (Path(__file__).parent / "sql" / "seed.sql")

    conn = get_conn()
    # run schema (CREATE TABLE ... IF NOT EXISTS)
    run_sql_file(conn, schema_path)
    # seed only if departments is empty (simple heuristic)
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM departments")
        dept_count = cur.fetchone()[0]
    except Exception:
        dept_count = 0
    if dept_count == 0:
        run_sql_file(conn, seed_path)
    conn.commit()
    conn.close()
    # ensure practice_log has expected columns
    ensure_practice_log_schema()
def update_excel_export():
    """
    Export the entire practice_log table to an Excel file.
    Called after every insert/update so Excel dashboard stays in sync.
    """
    conn = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT id, topic, question_title, query_text, user_note, rows_returned, exec_time_ms ,created_at  "
            "FROM practice_log ORDER BY id DESC",
            conn
        )
    finally:
        conn.close()

    export_path = Path(__file__).parent / "practice_log.xlsx"
    df.to_excel(export_path, index=False)

def ensure_practice_log_schema():
    """Add any missing expected columns to practice_log (safe ALTER TABLE for SQLite)."""
    conn = get_conn()
    cur = conn.cursor()
    existing = [r[1] for r in cur.execute("PRAGMA table_info(practice_log)").fetchall()]
    # expected columns (no timestamp)
    expected = {
        "topic": "TEXT",
        "question_title": "TEXT",
        "query_text": "TEXT",
        "user_note": "TEXT",
        "rows_returned": "INTEGER",
        "exec_time_ms": "INTEGER"
    }
    for col, col_type in expected.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE practice_log ADD COLUMN {col} {col_type}")
    conn.commit()
    conn.close()

def save_practice(topic, question, query_text, note, rows_returned, exec_time_ms, overwrite=False):
    """
    Save a practiced query.
    - overwrite=True: update the most recent row for (topic, question)
    - overwrite=False: insert a new row
    After saving, auto-export practice_log.xlsx for the Excel dashboard.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        if overwrite:
            row = cur.execute(
                "SELECT id FROM practice_log WHERE topic = ? AND question_title = ? "
                "ORDER BY id DESC LIMIT 1",
                (topic, question)
            ).fetchone()

            if row:
                last_id = row[0]
                cur.execute(
                    "UPDATE practice_log "
                    "SET query_text = ?, user_note = ?, rows_returned = ?, exec_time_ms = ? "
                    "WHERE id = ?",
                    (query_text, note, rows_returned, exec_time_ms, last_id)
                )
                conn.commit()
                # export after update
                update_excel_export()
                return "updated", last_id

        # otherwise insert new
        cur.execute(
            "INSERT INTO practice_log (topic, question_title, query_text, user_note, rows_returned, exec_time_ms,created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
            (topic, question, query_text, note, rows_returned, exec_time_ms)
        )
        new_id = cur.lastrowid
        conn.commit()
        # export after insert
        update_excel_export()
        return "inserted", new_id

    finally:
        conn.close()

def fetch_log(filter_topic=None):
    conn = get_conn()
    import pandas as pd
    if filter_topic and filter_topic != "All":
        df = pd.read_sql_query("SELECT id, topic, question_title, query_text, user_note FROM practice_log WHERE topic = ? ORDER BY id DESC", conn, params=(filter_topic,))
    else:
        df = pd.read_sql_query("SELECT id, topic, question_title, query_text, user_note FROM practice_log ORDER BY id DESC", conn)
    conn.close()
    return df
