import json
import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# app.py запускается из src/, .env лежит в корне проекта
if load_dotenv is not None:
    load_dotenv("../.env")


def is_llm_available() -> bool:
    return OpenAI is not None and bool(os.getenv("OPENAI_API_KEY"))


def answer_with_openai(question: str, context: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[LLM отключён: нет OPENAI_API_KEY.]"

    if OpenAI is None:
        return "[LLM отключён: пакет openai не установлен.]"

    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    try:
        client = OpenAI(api_key=api_key)

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты помощник по учебным планам магистратуры MLDS и MatMod. "
                        "Отвечай строго по предоставленному контексту. "
                        "Если в контексте нет ответа — скажи, что данных нет."
                    ),
                },
                {"role": "user", "content": f"Контекст:\n{context}\n\nВопрос: {question}"},
            ],
        )

        return resp.choices[0].message.content.strip()

    except Exception as e:
        return f"[LLM временно недоступен: {e}]"


def normalize_user_query(question: str):
   
    """
    Преобразует свободный вопрос пользователя в формат,
    удобный для поиска по базе.
    
    Возвращает dict или None, если LLM недоступен
    или не удалось распарсить ответ.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    print("[DEBUG api_key exists]", bool(api_key))
    print("[DEBUG OpenAI available]", OpenAI is not None)
    if not api_key or OpenAI is None:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    system_prompt = """
Ты помогаешь преобразовать вопрос пользователя к удобному формату для поиска по SQLite-базе дисциплин магистратуры.

Верни строго JSON без markdown и без пояснений.

Допустимые intent:
- list_courses
- course_info
- course_semester
- course_credits
- course_competencies
- course_learning_outcomes
- unknown

Формат ответа:
{
  "intent": "list_courses",
  "plan": "MatMod",
  "semester": 1,
  "course_name": null,
  "index_code": null,
  "field": null
}

Правила:
- Если пользователь спрашивает список предметов по семестру/программе -> list_courses
- Если спрашивает "о чем курс" -> course_info
- Если спрашивает "в каком семестре" -> course_semester
- Если спрашивает "сколько кредитов" -> course_credits
- Если спрашивает про компетенции -> course_competencies
- Если спрашивает про результаты обучения -> course_learning_outcomes
- Если не понял запрос -> unknown

plan:
- "MatMod", если пользователь пишет MatMod, МатМoд, матмoд, математическое моделирование
- "MLDS", если пользователь пишет MLDS, млдс, machine learning and data science
- null, если неясно

semester:
- 1, если пользователь пишет "первый семестр", "в 1 семестре", "в первом семестре"
- 2, если пользователь пишет "второй семестр", "во 2 семестре"
- 3, если пользователь пишет "третий семестр", "в 3 семестре"
- 4, если пользователь пишет "четвертый семестр", "в 4 семестре"
- иначе null

course_name:
- название курса, если можно выделить
- иначе null

index_code:
- код курса, если явно есть
- иначе null

field:
- можно оставить null
"""

    try:
        client = OpenAI(api_key=api_key)

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )

        content = resp.choices[0].message.content.strip()
        data = json.loads(content)

        return {
            "intent": data.get("intent"),
            "plan": data.get("plan"),
            "semester": data.get("semester"),
            "course_name": data.get("course_name"),
            "index_code": data.get("index_code"),
            "field": data.get("field"),
        }

    except Exception as e:
        print("[DEBUG normalize_user_query error]", e)
        return None