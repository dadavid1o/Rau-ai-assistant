from db import init_db, get_conn
from llm import answer_with_openai
from import_csv import import_courses


def _variants(word: str):
    w = word.strip()
    vs = {w}
    vs.add(w.lower())
    if w:
        vs.add(w[0].upper() + w[1:])
    return list(vs)


def search_courses(question: str, top_k: int = 3):
    raw_words = [w.strip() for w in question.replace("?", " ").replace(",", " ").split() if len(w.strip()) >= 2]
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

    sql = f"""
        SELECT id, plan, index_code, name, semester, credits, course_type,
               description, learning_outcomes, aliases, source
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
            f"COURSE: {r['name']}\n"
            f"Semester: {r['semester']}, Credits: {r['credits']}, Type: {r['course_type']}\n"
            f"Description: {r['description']}\n"
            f"Learning outcomes: {r['learning_outcomes']}\n"
            f"Source: {r['source']}\n"
        )
    return "\n---\n".join(parts)


def main() -> None:
    init_db()

    import_courses("../data/mlds_skeleton.csv")
    print("Консольный ассистент. Введи вопрос или 'exit'.")

    while True:
        q = input("> ").strip()
        if q.lower() in ("exit", "quit"):
            break

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
