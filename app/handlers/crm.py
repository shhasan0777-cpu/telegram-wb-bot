import csv
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.config import get_settings
from app.keyboards.common import crm_keyboard
from app.repositories.crm import get_lead, list_leads_by_status, upsert_lead, all_leads

router = Router()
def is_admin(user_id:int)->bool: return user_id == get_settings().admin_id

@router.message(F.text == "/crm")
async def crm_panel(message: Message):
    if is_admin(message.from_user.id): await message.answer("📋 CRM-панель:", reply_markup=crm_keyboard())

@router.callback_query(F.data.startswith("crm_"))
async def crm_actions(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    action=callback.data.replace("crm_",""); status_map={"hot":"hot","warm":"warm","cold":"cold","ready":"ready_to_buy"}
    if action=="export": await export_crm(callback.message); await callback.answer(); return
    if action=="callback": leads=list_leads_by_status(callback_only=True)
    elif action in status_map: leads=list_leads_by_status(status_map[action])
    else: await callback.answer(); return
    if not leads: await callback.message.answer("Пока нет лидов в этом разделе."); await callback.answer(); return
    text="📋 Лиды:\n\n"
    for lead in leads:
        user_id, username, status, interest, budget, next_action_at = lead
        text += f"👤 User ID: {user_id}\nUsername: @{username or 'нет'}\nСтатус: {status or 'new'}\nИнтерес: {interest or 'не указан'}\nБюджет: {budget or 'не указан'}\nСлед. действие: {next_action_at or 'не указано'}\n──────────────\n"
    await callback.message.answer(text); await callback.answer()

@router.message(F.text.startswith("/lead"))
async def show_lead(message: Message):
    if not is_admin(message.from_user.id): return
    try:
        lead=get_lead(int(message.text.split()[1]))
        if not lead: await message.answer("Лид не найден."); return
        await message.answer(f"👤 Карточка лида\n\nUser ID: {lead[0]}\nUsername: @{lead[1] or 'нет'}\nИмя: {lead[2] or 'не указано'}\nТелефон: {lead[3] or 'не указан'}\nИнтерес: {lead[4] or 'не указан'}\nБюджет: {lead[5] or 'не указан'}\nСтатус: {lead[6] or 'new'}\nБоль: {lead[7] or 'не указана'}\nСлед. действие: {lead[8] or 'не указано'}\nКогда: {lead[9] or 'не указано'}\nЗаметка: {lead[10] or 'нет'}\n\nСоздан: {lead[11]}\nОбновлён: {lead[12]}")
    except Exception: await message.answer("Используй:\n/lead USER_ID\n\nПример:\n/lead 7174605359")

@router.message(F.text.startswith("/note"))
async def add_note(message: Message):
    if not is_admin(message.from_user.id): return
    try:
        _,uid,note=message.text.split(" ",2); upsert_lead(int(uid), manager_note=note); await message.answer("✅ Заметка добавлена.")
    except Exception: await message.answer("Используй:\n/note USER_ID текст заметки")

@router.message(F.text.startswith("/setstatus"))
async def set_status(message: Message):
    if not is_admin(message.from_user.id): return
    try:
        _,uid,status=message.text.split()[:3]
        if status not in ["cold","warm","hot","ready_to_buy"]: await message.answer("Статусы:\ncold\nwarm\nhot\nready_to_buy"); return
        upsert_lead(int(uid), status=status); await message.answer(f"✅ Статус пользователя {uid} обновлён на {status}")
    except Exception: await message.answer("Используй:\n/setstatus USER_ID STATUS")

@router.message(F.text.startswith("/callback"))
async def set_callback(message: Message):
    if not is_admin(message.from_user.id): return
    try:
        _,uid,when=message.text.split(" ",2); upsert_lead(int(uid), next_action="перезвонить", next_action_at=when); await message.answer("✅ Перезвон добавлен.")
    except Exception: await message.answer("Используй:\n/callback USER_ID когда\n\nПример:\n/callback 7174605359 завтра 15:00")

async def export_crm(message: Message):
    leads=all_leads()
    with open("crm_export.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["user_id","username","name","phone","interest","budget","status","pain","next_action","next_action_at","manager_note","created_at","updated_at"]); w.writerows(leads)
    await message.answer_document(FSInputFile("crm_export.csv"))
