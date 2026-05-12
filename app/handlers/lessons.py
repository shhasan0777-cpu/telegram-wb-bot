from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from app.data.lessons import LESSONS
from app.repositories.users import get_user, update_user
from app.repositories.analytics import log_event, has_event
from app.repositories.scheduled_tasks import schedule_task
from app.repositories.crm import upsert_lead
from app.keyboards.common import lesson_keyboard, final_keyboard, start_keyboard
from app.handlers.start import notify_admin

router = Router()

def check_deadline(user_id:int)->bool:
    user=get_user(user_id)
    if not user or not user["access_deadline"]: return True
    for fmt in ["%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S"]:
        try: return datetime.now() <= datetime.strptime(user["access_deadline"], fmt)
        except Exception: pass
    return True

async def send_lesson(bot: Bot, user_id:int, lesson_num:int):
    if not check_deadline(user_id):
        await bot.send_message(user_id, "⛔️ Бесплатный доступ истёк\n\nЧтобы продолжить обучение — переходи 👇", reply_markup=final_keyboard()); return
    lesson=LESSONS[lesson_num]
    update_user(user_id, current_lesson=lesson_num); log_event(user_id, f"lesson_{lesson_num}")
    if lesson_num==1: update_user(user_id, segment="cold")
    elif lesson_num==2:
        update_user(user_id, segment="warm")
        if not has_event(user_id,"lesson_2_reminder_scheduled"):
            schedule_task(user_id,"lesson_2_reminder",(datetime.now()+timedelta(hours=6)).isoformat(timespec="seconds")); log_event(user_id,"lesson_2_reminder_scheduled")
    elif lesson_num==3:
        update_user(user_id, segment="hot"); await notify_admin(bot, f"🔥 Горячий пользователь дошёл до 3 урока: {user_id}")
    await bot.send_message(user_id, f"🎬 {lesson['title']}\n\n{lesson['description']}\n\n👇 Смотри видео\n\n🔥 Дальше будет важнее")
    try: await bot.send_video(user_id, lesson["file_id"], reply_markup=lesson_keyboard(lesson_num, lesson["vk_url"]))
    except Exception: await bot.send_message(user_id, "⚠️ Видео не загрузилось.\nСмотри через VK 👇", reply_markup=lesson_keyboard(lesson_num, lesson["vk_url"]))

@router.callback_query(F.data == "free_lessons")
async def free_lessons(callback: CallbackQuery, bot: Bot):
    user_id=callback.from_user.id; user=get_user(user_id); current=user["current_lesson"] or 0
    if current>0:
        await callback.message.answer(f"Продолжаем с урока {current} 👇"); await send_lesson(bot,user_id,current)
    else:
        await callback.message.answer("Открываю первый бесплатный урок 👇"); await send_lesson(bot,user_id,1)
        user=get_user(user_id)
        if user["funnel_started"]==0:
            update_user(user_id, funnel_started=1)
            delays=[1,24,48,72,96,120,144]
            for day,h in enumerate(delays, start=1): schedule_task(user_id, f"week_funnel_day_{day}", (datetime.now()+timedelta(hours=h)).isoformat(timespec="seconds"))
    await callback.answer()

@router.callback_query(F.data == "continue")
async def continue_handler(callback: CallbackQuery, bot: Bot):
    user=get_user(callback.from_user.id)
    if user and user["current_lesson"]>0:
        await callback.message.answer(f"Продолжаем с урока {user['current_lesson']} 👇"); await send_lesson(bot, callback.from_user.id, user["current_lesson"])
    else: await callback.message.answer("Сначала подпишись на канал 👇", reply_markup=start_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("next_"))
async def next_lesson(callback: CallbackQuery, bot: Bot):
    await callback.answer("Открываю следующий урок...")
    nxt=int(callback.data.split("_")[1])+1
    if nxt<=3: await send_lesson(bot, callback.from_user.id, nxt)

@router.callback_query(F.data == "getcourse")
async def getcourse(callback: CallbackQuery, bot: Bot):
    user_id=callback.from_user.id; log_event(user_id,"getcourse"); update_user(user_id, segment="ready_to_buy")
    await notify_admin(bot, f"💰 ЧЕЛ ГОТОВ КУПИТЬ!\n\nUser ID: {user_id}\nUsername: @{callback.from_user.username or 'нет'}\nНажал GetCourse")
    await callback.message.answer("🔥 Ты дошёл до конца бесплатной части.\n\nСейчас у тебя есть база.\nНо чтобы реально выйти на доход — нужна система.\n\n👇 Переходи или оставь заявку.", reply_markup=final_keyboard())
    await callback.answer()

@router.callback_query(F.data == "lead")
async def lead(callback: CallbackQuery, bot: Bot):
    user_id=callback.from_user.id; username=callback.from_user.username
    log_event(user_id,"lead"); update_user(user_id, segment="ready_to_buy")
    upsert_lead(user_id, username, status="ready_to_buy", interest="обучение Wildberries")
    await notify_admin(bot, f"📩 Новая заявка!\n\nUser ID: {user_id}\nUsername: @{username or 'нет'}")
    await callback.message.answer("✅ Заявка отправлена. Менеджер скоро свяжется с тобой."); await callback.answer()
