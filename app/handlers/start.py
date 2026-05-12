from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from app.config import get_settings
from app.repositories.users import save_user, get_user, update_user
from app.repositories.analytics import log_event
from app.keyboards.common import start_keyboard, after_sub_keyboard, final_keyboard

router = Router()

async def notify_admin(bot: Bot, text: str):
    admin_id = get_settings().admin_id
    if admin_id:
        try: await bot.send_message(admin_id, text)
        except Exception: pass

async def is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(get_settings().channel_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

@router.message(CommandStart())
async def start(message: Message, bot: Bot):
    user_id=message.from_user.id; username=message.from_user.username
    save_user(user_id, username); log_event(user_id, "start")
    await notify_admin(bot, f"👤 Новый пользователь:\nID: {user_id}\nUsername: @{username or 'нет'}")
    await message.answer("Привет 👋\n\nЯ бот от TojikonSmart.\n\nЯ помогу тебе:\n🧮 посчитать юнит-экономику товара на Wildberries\n🎓 получить бесплатные уроки по старту на WB\n📦 разобраться с товаром, кабинетом продавца и первыми шагами\n\nЧтобы продолжить, сначала подпишись на наш канал 👇", reply_markup=start_keyboard())

@router.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery, bot: Bot):
    user_id=callback.from_user.id; username=callback.from_user.username
    save_user(user_id, username)
    if not await is_subscribed(bot, user_id):
        await callback.message.answer("❌ Подписка не найдена.\n\nСначала подпишись на канал, потом нажми кнопку проверки 👇", reply_markup=start_keyboard())
        await callback.answer(); return
    log_event(user_id,"subscribed")
    user=get_user(user_id)
    if not user["access_deadline"]:
        update_user(user_id, access_deadline=(datetime.now()+timedelta(days=7)).strftime("%d.%m.%Y %H:%M"))
    await callback.message.answer("Подписка подтверждена ✅\n\nЧто хочешь сделать сейчас?", reply_markup=after_sub_keyboard())
    await callback.answer()
