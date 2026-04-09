import sqlite3
from pathlib import Path
from typing import Optional


DB_PATH = Path(__file__).resolve().parent.parent / "courses.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan TEXT NOT NULL,
            index_code TEXT NOT NULL,
            name TEXT NOT NULL,
            semester INTEGER,
            credits INTEGER,
            course_type TEXT,
            department TEXT,
            competencies TEXT,
            description TEXT,
            learning_outcomes TEXT,
            aliases TEXT,
            source TEXT,
            UNIQUE (plan, index_code, semester)
        );
        """)
        conn.commit()
def courses_count() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM courses;").fetchone()
        return int(row["c"])

def insert_course(
    name: str,
    semester: Optional[int],
    credits: Optional[int],
    course_type: str,
    description: str,
    learning_outcomes: str,
    source: str = ""
) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO courses
              (name, semester, credits, course_type, description, learning_outcomes, source)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (name, semester, credits, course_type, description, learning_outcomes, source))
        conn.commit()
def get_courses_by_plan_and_semester(plan: str, semester: int):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, plan, index_code, name, semester, credits, course_type,
                   description, learning_outcomes, competencies, aliases, source
            FROM courses
            WHERE plan = ? AND semester = ?
            ORDER BY index_code;
        """, (plan, semester)).fetchall()
        return list(rows)


def get_course_by_name_or_code(course_name: Optional[str] = None, index_code: Optional[str] = None):
    with get_conn() as conn:
        if index_code:
            rows = conn.execute("""
                SELECT id, plan, index_code, name, semester, credits, course_type,
                       description, learning_outcomes, competencies, aliases, source
                FROM courses
                WHERE index_code = ?
                ORDER BY semester
                LIMIT 5;
            """, (index_code,)).fetchall()
            return list(rows)

        if course_name:
            like = f"%{course_name}%"
            rows = conn.execute("""
                SELECT id, plan, index_code, name, semester, credits, course_type,
                       description, learning_outcomes, competencies, aliases, source
                FROM courses
                WHERE name LIKE ?
                   OR aliases LIKE ?
                   OR description LIKE ?
                ORDER BY semester
                LIMIT 5;
            """, (like, like, like)).fetchall()
            return list(rows)

        return []