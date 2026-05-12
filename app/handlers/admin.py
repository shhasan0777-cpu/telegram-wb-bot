import csv
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.config import get_settings
from app.db.connection import db
from app.keyboards.common import admin_keyboard, broadcast_keyboard
from app.services.broadcast import safe_send_message

router = Router()

def is_admin(user_id:int)->bool: return user_id == get_settings().admin_id

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if is_admin(message.from_user.id): await message.answer("⚙️ Админ-панель:", reply_markup=admin_keyboard())

@router.message(F.text == "/stats")
async def stats_cmd(message: Message):
    if is_admin(message.from_user.id): await send_stats(message)

@router.message(F.text == "/export")
async def export_cmd(message: Message):
    if is_admin(message.from_user.id): await export_database(message)

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await send_stats(callback.message); await callback.answer()

@router.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await export_database(callback.message); await callback.answer()

@router.callback_query(F.data.startswith("admin_broadcast"))
async def admin_broadcast_info(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.message.answer("Для рассылки используй команды:\n\n/broadcast all текст\n/broadcast lesson1 текст\n/broadcast lesson2 текст\n/broadcast lesson3 текст\n/broadcast hot текст\n/broadcast warm текст\n/broadcast cold текст\n\nБез кнопок:\n/broadcast_nobutton all текст")
    await callback.answer()

async def send_stats(message: Message):
    with db() as conn:
        users=conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        l1=conn.execute("SELECT COUNT(*) FROM analytics WHERE event='lesson_1'").fetchone()[0]
        l2=conn.execute("SELECT COUNT(*) FROM analytics WHERE event='lesson_2'").fetchone()[0]
        l3=conn.execute("SELECT COUNT(*) FROM analytics WHERE event='lesson_3'").fetchone()[0]
        gc=conn.execute("SELECT COUNT(*) FROM analytics WHERE event='getcourse'").fetchone()[0]
        leads=conn.execute("SELECT COUNT(*) FROM analytics WHERE event='lead'").fetchone()[0]
        cold=conn.execute("SELECT COUNT(*) FROM users WHERE segment='cold'").fetchone()[0]
        warm=conn.execute("SELECT COUNT(*) FROM users WHERE segment='warm'").fetchone()[0]
        hot=conn.execute("SELECT COUNT(*) FROM users WHERE segment='hot'").fetchone()[0]
        ready=conn.execute("SELECT COUNT(*) FROM users WHERE segment='ready_to_buy'").fetchone()[0]
    await message.answer(f"📊 Статистика:\n\n👥 Пользователи: {users}\n🎬 Урок 1: {l1}\n🎬 Урок 2: {l2}\n🎬 Урок 3: {l3}\n💰 GetCourse: {gc}\n📩 Заявки: {leads}\n\n❄️ Cold: {cold}\n🌤 Warm: {warm}\n🔥 Hot: {hot}\n💰 Ready to buy: {ready}")

async def export_database(message: Message):
    with db() as conn:
        users=conn.execute("SELECT * FROM users").fetchall(); analytics=conn.execute("SELECT user_id,event,created_at FROM analytics").fetchall()
    with open("users_export.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["user_id","username","current_lesson","stage","funnel_started","segment","access_deadline"]); w.writerows(users)
    with open("analytics_export.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["user_id","event","created_at"]); w.writerows(analytics)
    await message.answer_document(FSInputFile("users_export.csv")); await message.answer_document(FSInputFile("analytics_export.csv"))

@router.message(F.text.startswith("/extend_user"))
async def extend_user(message: Message):
    if not is_admin(message.from_user.id): return
    from datetime import datetime, timedelta
    from app.repositories.users import update_user
    try:
        _,uid,days=message.text.split()[:3]
        deadline=(datetime.now()+timedelta(days=int(days))).strftime("%d.%m.%Y %H:%M")
        update_user(int(uid), access_deadline=deadline); await message.answer(f"✅ Доступ продлён до {deadline}")
    except Exception: await message.answer("Используй:\n/extend_user USER_ID ДНИ")

@router.message(F.text.startswith("/restart_user"))
async def restart_user(message: Message):
    if not is_admin(message.from_user.id): return
    from app.repositories.users import update_user
    try:
        uid=int(message.text.split()[1]); update_user(uid,current_lesson=0,funnel_started=0,segment="cold"); await message.answer(f"✅ Пользователь {uid} сброшен.")
    except Exception: await message.answer("Используй:\n/restart_user USER_ID")

@router.message(F.text.startswith("/broadcast_nobutton"))
async def broadcast_nobutton(message: Message, bot: Bot):
    if is_admin(message.from_user.id): await send_broadcast(message, bot, message.text.replace("/broadcast_nobutton","").strip(), False)

@router.message(F.text.startswith("/broadcast"))
async def broadcast(message: Message, bot: Bot):
    if is_admin(message.from_user.id): await send_broadcast(message, bot, message.text.replace("/broadcast","").strip(), True)

async def send_broadcast(message: Message, bot: Bot, text: str, with_buttons=True):
    if not text:
        await message.answer("Использование:\n\n/broadcast all текст\n/broadcast lesson1 текст\n/broadcast lesson2 текст\n/broadcast lesson3 текст\n/broadcast hot текст\n/broadcast warm текст\n/broadcast cold текст"); return
    parts=text.split(" ",1); segment=parts[0]; broadcast_text=parts[1] if len(parts)>1 else ""
    if not broadcast_text: await message.answer("Напиши текст рассылки после сегмента."); return
    with db() as conn:
        maps={"all":"SELECT user_id FROM users","lesson1":"SELECT user_id FROM users WHERE current_lesson >= 1","lesson2":"SELECT user_id FROM users WHERE current_lesson >= 2","lesson3":"SELECT user_id FROM users WHERE current_lesson >= 3"}
        if segment in maps: users=conn.execute(maps[segment]).fetchall()
        elif segment in ["cold","warm","hot","ready_to_buy"]: users=conn.execute("SELECT user_id FROM users WHERE segment=?",(segment,)).fetchall()
        else: await message.answer("Сегмент: all, lesson1, lesson2, lesson3, cold, warm, hot, ready_to_buy"); return
    sent=0
    for u in users:
        ok=await safe_send_message(bot, u[0], broadcast_text, reply_markup=broadcast_keyboard() if with_buttons else None)
        if ok: sent += 1
    await message.answer(f"✅ Рассылка отправлена: {sent} пользователям")
