import os
from openai import OpenAI
from dotenv import load_dotenv

# запускаем app.py из src/ и он импортирует этот файл, так что .env лежит в корне проекта 
load_dotenv("../.env")

def answer_with_openai(question: str, context: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[LLM отключён: нет OPENAI_API_KEY.]"

    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    try:
        client = OpenAI(api_key=api_key)

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты помощник по учебному плану магистратуры MLDS. "
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