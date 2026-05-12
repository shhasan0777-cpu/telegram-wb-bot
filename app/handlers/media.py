import os
from aiogram import Router, F, Bot
from aiogram.types import Message
from app.config import get_settings
from app.services.crm_ai import groq_client, ai_parse_crm_text
from app.repositories.crm import find_lead, update_lead_smart

router = Router()
def is_admin(user_id:int)->bool: return user_id == get_settings().admin_id

@router.message(F.voice)
async def manager_voice(message: Message, bot: Bot):
    if not is_admin(message.from_user.id): return
    try:
        file = await bot.get_file(message.voice.file_id)
        os.makedirs("voices", exist_ok=True)
        save_path = f"voices/{message.voice.file_id}.ogg"
        await bot.download_file(file.file_path, save_path)
        with open(save_path, "rb") as audio_file:
            transcription = groq_client().audio.transcriptions.create(file=audio_file, model="whisper-large-v3")
        text = transcription.text
        data = ai_parse_crm_text(text)
        user_id = data.get("user_id") or find_lead(data)
        if not user_id:
            await message.answer(f"🎙 Я понял голосовое, но не понял к какому клиенту привязать.\n\nРасшифровка:\n{text}\n\nСкажи имя, username, телефон или user ID клиента."); return
        update_lead_smart(int(user_id), data)
        await message.answer(f"✅ CRM обновлена из голосового.\n\n👤 User ID: {user_id}\nUsername: @{data.get('username') or 'не указан'}\nИмя: {data.get('name') or 'не указано'}\nТелефон: {data.get('phone') or 'не указан'}\nСтатус: {data.get('status') or 'не изменён'}\nИнтерес: {data.get('interest') or 'не изменён'}\nБюджет: {data.get('budget') or 'не изменён'}\nБоль: {data.get('pain') or 'не изменена'}\nСлед. действие: {data.get('next_action') or 'не изменено'}\nКогда: {data.get('next_action_at') or 'не изменено'}\nЗаметка: {data.get('manager_note') or 'не изменена'}\n\n📝 Расшифровка:\n{text}")
    except Exception as e:
        await message.answer(f"❌ Ошибка AI CRM:\n{e}")

@router.message(F.video)
async def get_video_file_id(message: Message):
    if is_admin(message.from_user.id): await message.answer(f"file_id этого видео:\n\n{message.video.file_id}")
