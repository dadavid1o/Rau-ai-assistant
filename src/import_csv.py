import csv
from pathlib import Path
from db import init_db, get_conn

def import_courses(csv_path: str) -> int:
    init_db()
    path = Path(csv_path)

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    inserted = 0
    with get_conn() as conn:
        for r in rows:
            plan = (r.get("plan") or "").strip()
            index_code = (r.get("index_code") or "").strip()
            name = (r.get("name") or "").strip()

            # Без этих полей запись бессмысленна
            if not plan or not index_code or not name:
                continue

            semester = (r.get("semester") or "").strip()
            credits = (r.get("credits") or "").strip()

            semester_val = int(semester) if semester.isdigit() else None
            credits_val = int(credits) if credits.isdigit() else None

            conn.execute("""
                INSERT INTO courses (
                    plan, index_code, name,
                    semester, credits, course_type,
                    department, competencies,
                    description, learning_outcomes, aliases,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(plan, index_code, semester) DO UPDATE SET
                    name=excluded.name,
                    semester=excluded.semester,
                    credits=excluded.credits,
                    course_type=excluded.course_type,
                    department=excluded.department,
                    competencies=excluded.competencies,
                    description=excluded.description,
                    learning_outcomes=excluded.learning_outcomes,
                    aliases=excluded.aliases,
                    source=excluded.source;
            """, (
                plan,
                index_code,
                name,
                semester_val,
                credits_val,
                (r.get("course_type") or "").strip(),
                (r.get("department") or "").strip(),
                (r.get("competencies") or "").strip(),
                (r.get("description") or "").strip(),
                (r.get("learning_outcomes") or "").strip(),
                (r.get("aliases") or "").strip(),
                (r.get("source") or "").strip(),
            ))
            inserted += 1

        conn.commit()

    return inserted