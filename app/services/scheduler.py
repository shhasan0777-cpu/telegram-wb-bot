import asyncio, logging
from datetime import datetime
from aiogram import Bot
from app.repositories.scheduled_tasks import due_tasks, mark_done, mark_failed
from app.repositories.users import get_user
from app.repositories.analytics import has_event
from app.keyboards.common import final_keyboard

log=logging.getLogger(__name__)

FUNNEL_TEXTS={
    "week_funnel_day_1":("👀 Ты начал обучение. Не останавливайся — следующий урок может сэкономить тебе деньги на ошибках.", False),
    "week_funnel_day_2":("🔥 День 2: многие новички сливаются не из-за товара, а из-за отсутствия системы. Дойди до 3 урока.", False),
    "week_funnel_day_3":("⚡️ День 3: если хочешь стартовать быстрее, можешь перейти в полную программу.", True),
    "week_funnel_day_4":("📌 День 4: в полной программе разбираем товар, карточку, рекламу и первые продажи.", True),
    "week_funnel_day_5":("⏳ День 5: места на сопровождение ограничены. Лучше не откладывать старт.", True),
    "week_funnel_day_6":("💬 День 6: хочешь, чтобы менеджер подсказал по обучению? Оставь заявку.", True),
    "week_funnel_day_7":("🚀 День 7: бесплатный доступ подходит к концу.\n\nДальше лучше идти по системе, чтобы не сливать время и деньги.", True),
}

async def run_task(bot: Bot, task):
    t=task["task_type"]; uid=task["user_id"]
    if t=="lesson_2_reminder":
        user=get_user(uid)
        if user and user["current_lesson"]==2 and not has_event(uid,"lesson_3"):
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await bot.send_message(uid, "👀 Ты остановился на 2 уроке.\n\nСамое важное — в 3 уроке: там разбор выбора ниши и товара.\nНе бросай на середине 👇", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Перейти к 3 уроку ➡️", callback_data="next_2")]]))
    elif t in FUNNEL_TEXTS:
        text, with_kb = FUNNEL_TEXTS[t]
        await bot.send_message(uid, text, reply_markup=final_keyboard() if with_kb else None)

async def scheduler_loop(bot: Bot):
    while True:
        now=datetime.now().isoformat(timespec="seconds")
        for task in due_tasks(now):
            try:
                await run_task(bot, task)
                mark_done(task["id"])
            except Exception as e:
                log.exception("Scheduled task failed")
                mark_failed(task["id"], str(e))
        await asyncio.sleep(30)
