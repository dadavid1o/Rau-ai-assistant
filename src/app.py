from db import (
    init_db,
    get_conn,
    get_courses_by_plan_and_semester,
    get_course_by_name_or_code,   
)
from llm import answer_with_openai, normalize_user_query
from import_csv import import_courses


def _variants(word: str):
    w = word.strip()
    vs = {w}
    vs.add(w.lower())
    if w:
        vs.add(w[0].upper() + w[1:])
    return list(vs)


def search_courses(question: str, top_k: int = 3):
    STOP = {
        "в", "во", "на", "и", "или", "а", "но", "что", "это", "как", "какой", "каком",
        "какая", "какие", "сколько", "где", "когда", "ли", "по", "для", "о", "об",
        "семестр", "семестре", "з.е", "зе", "з.е.", "кредитов", "кредита", "кредиты",
        "курс", "курса", "курсе", "чем", "про", "расскажи", "объясни", "поясни"
    }

    tokens = [w.strip() for w in question.replace("?", " ").replace(",", " ").split() if w.strip()]
    raw_words = []
    for t in tokens:
        tl = t.lower().strip(".")
        if tl in STOP:
            continue
        if len(t) >= 2:
            raw_words.append(t)
    if not raw_words:
        return []

    plan_filter = None
    filtered = []
    for w in raw_words:
        wl = w.lower()
        if wl == "mlds":
            plan_filter = "MLDS"
        elif wl == "matmod":
            plan_filter = "MatMod"
        else:
            filtered.append(w)
    raw_words = filtered

    if not raw_words:
        return []

    clauses = []
    params = []

    for w in raw_words:
        vs = _variants(w)
        sub = []
        for v in vs:
            like = f"%{v}%"
            sub.append("(index_code LIKE ? OR name LIKE ? OR description LIKE ? OR learning_outcomes LIKE ? OR aliases LIKE ?)")
            params.extend([like, like, like, like, like])
        clauses.append("(" + " OR ".join(sub) + ")")

    where_sql = " AND ".join(clauses)
    if plan_filter is not None:
        where_sql = f"(plan = ?) AND ({where_sql})"
        params.insert(0, plan_filter)

    sql = f"""
        SELECT id, plan, index_code, name, semester, credits, course_type,
               description, learning_outcomes, competencies, aliases, source
        FROM courses
        WHERE {where_sql}
        LIMIT ?;
    """
    params.append(top_k)

    with get_conn() as conn:
        return list(conn.execute(sql, params).fetchall())


def format_context(rows) -> str:
    parts = []
    for r in rows:
        parts.append(
            f"CODE: {r['plan']} {r['index_code']}\n"
            f"COURSE: {r['name']}\n"
            f"Semester: {r['semester']}, Credits: {r['credits']}, Type: {r['course_type']}\n"
            f"Description: {r['description']}\n"
            f"Learning outcomes: {r['learning_outcomes']}\n"
            f"Competencies: {r['competencies']}\n"
            f"Source: {r['source']}\n"
        )
    return "\n---\n".join(parts)


def main() -> None:
    init_db()

    import_courses("../data/mlds_skeleton.csv")
    import_courses("../data/matmod_skeleton.csv")
    print("Консольный ассистент. Введи вопрос или 'exit'.")

    while True:
        q = input("> ").strip()
        if q.lower() in ("exit", "quit"):
            break

        normalized = normalize_user_query(q)
        print("[DEBUG normalize_user_query]", normalized)
        rows = []

        if normalized is not None:
            intent = normalized.get("intent")
            plan = normalized.get("plan")
            semester = normalized.get("semester")
            course_name = normalized.get("course_name")
            index_code = normalized.get("index_code")

            if intent == "list_courses" and plan and semester:
                rows = get_courses_by_plan_and_semester(plan, semester)

            elif intent in (
                "course_info",
                "course_semester",
                "course_credits",
                "course_competencies",
                "course_learning_outcomes",
            ):
                rows = get_course_by_name_or_code(
                    course_name=course_name,
                    index_code=index_code,
                )

        if not rows:
            rows = search_courses(q, top_k=3)

        if not rows:
            print("В базе нет подходящих данных. Попробуй переформулировать.")
            continue

        context = format_context(rows)
        print("\n[Найденный контекст]")
        print(context)

        print("\n[Ответ ассистента]")
        print(answer_with_openai(q, context))


if __name__ == "__main__":
    main()
