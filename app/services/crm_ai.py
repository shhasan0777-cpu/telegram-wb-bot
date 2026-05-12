import json, re
from groq import Groq
from app.config import get_settings


def groq_client():
    return Groq(api_key=get_settings().groq_api_key)


def ai_parse_crm_text(text: str) -> dict:
    prompt = f"""
Ты AI-ассистент CRM для Telegram-бота обучения Wildberries.
Задача: понять команду менеджера и вернуть JSON.
ВАЖНО: Не требуй все данные. Если поле не названо — верни null. Статусы: холодный=cold, тёплый=warm, горячий=hot, готов купить=ready_to_buy.
Верни ТОЛЬКО JSON без пояснений:
{{"user_id": null, "username": null, "name": null, "phone": null, "interest": null, "budget": null, "status": null, "pain": null, "next_action": null, "next_action_at": null, "manager_note": null}}
Текст менеджера:
{text}
"""
    r = groq_client().chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}], temperature=0)
    content = re.sub(r"```json|```", "", r.choices[0].message.content.strip()).strip()
    return json.loads(content)
