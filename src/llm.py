import json
import os

try:
    from google import genai
except ImportError:
    genai = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# app.py запускаю из src/, .env лежит в корне проекта
if load_dotenv is not None:
    load_dotenv("../.env")


def is_llm_available() -> bool:
    return genai is not None and bool(os.getenv("GEMINI_API_KEY"))


def answer_with_openai(question: str, context: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")

    if genai is None:
        print("LLM Пакет google-genai не установлен. Генерация ответа недоступна")
        return "[LLM отключён: пакет google-genai не установлен]"

    if not api_key:
        print("LLM GEMINI_API_KEY не найден. Генерация ответа недоступна.")
        return "[LLM отключён: нет GEMINI_API_KEY.]"

    model="gemini-2.5-flash"

    try:
        client = genai.Client(api_key=api_key)

        prompt = (
           "Ты помощник по учебным планам магистратуры MLDS и MatMod. "
           "Отвечай строго по предоставленному контексту. "
           "Не добавляй факты от себя. "
           "Не дoдумывай отсутствующую информацию. "
           "Если в контексте нет ответа — скажи, что данных нет. "
           "Старайся минимально переформулировать найденные данные и не искажать их смысл.\n\n"
            f"Контекст:\n{context}\n\n"
            f"Вопрос: {question}"
        )

        resp = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        return resp.text.strip()

    except Exception as e:
        print(f"LLM Не удалось получить ответ от Gemini: {e}")
        return f"[LLM временно недоступен: {e}]"


def normalize_user_query(question: str):
    """
    преобразует вопрос пользователя в формат,
    удобный для поиска по базе.

    возвращает dict или None
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if genai is None:
        print("LLM Пакет google-genai не установлен. AI-нормализация запроса недоступна.")
        return None

    if not api_key:
        print("LLM GEMINI_API_KEY не найден. AI-нормализация запроса недоступна.")
        return None

    model="gemini-2.5-flash"

    prompt = """
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
- "MatMod", если пользователь пишет MatMod, МатМод, матмод, математическое моделирование
- "MLDS", если пользователь пишет MLDS, млдс, machine learning and data science
- null, если неясно

semester:
- 1, если пользователь пишет "первый семестр", "в 1 семестре", "в первом семестре"
- 2, если пользователь пишет "второй семестр", "во 2 семестре", "во втором семестре"
- 3, если пользователь пишет "третий семестр", "в 3 семестре", "в третьем семестре"
- 4, если пользователь пишет "четвертый семестр", "в 4 семестре", "в четвертом семестре"
- иначе null

course_name:
- название курса, если можно выделить
- иначе null

index_code:
- код курса, если явно есть
- иначе null

field:
- можно оставить null

Вопрос пользователя:
""" + question

    try:
        client = genai.Client(api_key=api_key)

        resp = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        content = resp.text.strip()
        print("[LLM RAW NORMALIZE RESPONSE]", content)
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()
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
        print(f"LLM Не удалось нормализовать запрос через Gemini: {e}")
        return None