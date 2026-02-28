import os
from openai import OpenAI

def answer_with_openai(question: str, context: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
      return "[LLM отключён: нет OPENAI_API_KEY. Сейчас работаю только в режиме поиска.]"
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OPENAI_API_KEY не найден. Установи переменную окружения и попробуй снова."

    client = OpenAI(api_key=api_key)

    system = (
        "Ты академический ассистент магистерской программы. "
        "Отвечай строго на основе предоставленного КОНТЕКСТА из базы курсов. "
        "Если в контексте нет ответа — так и скажи: 'В базе нет информации для точного ответа'. "
        "Не выдумывай."
    )

    user = f"КОНТЕКСТ:\n{context}\n\nВОПРОС:\n{question}\n\nОТВЕТ:"

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    return resp.choices[0].message.content.strip()
