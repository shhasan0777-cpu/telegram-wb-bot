import math
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config import get_settings
from app.data.wb import FBO_WAREHOUSES


def start_keyboard():
    s=get_settings()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подписаться на канал 📢", url=s.channel_url)],
        [InlineKeyboardButton(text="Я подписался ✅", callback_data="check_sub")]
    ])

def after_sub_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧮 Посчитать юнитку WB", callback_data="unit_start")],
        [InlineKeyboardButton(text="🎓 Получить бесплатные уроки", callback_data="free_lessons")]
    ])

def lesson_keyboard(lesson_num, vk_url):
    buttons = [[InlineKeyboardButton(text="Не открывается? Смотреть в VK", url=vk_url)]]
    if lesson_num < 3:
        buttons.append([InlineKeyboardButton(text="Следующий урок ➡️", callback_data=f"next_{lesson_num}")])
    else:
        buttons.append([InlineKeyboardButton(text="Хочу продолжить обучение 🚀", callback_data="getcourse")])
        buttons.append([InlineKeyboardButton(text="Оставить заявку менеджеру 💬", callback_data="lead")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def final_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в GetCourse 🔥", url=get_settings().getcourse_url)],
        [InlineKeyboardButton(text="Оставить заявку менеджеру 💬", callback_data="lead")]
    ])

def broadcast_keyboard():
    return final_keyboard()

def continue_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Продолжить обучение ▶️", callback_data="continue")]])

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📁 Экспорт базы", callback_data="admin_export")],
        [InlineKeyboardButton(text="📢 Рассылка всем", callback_data="admin_broadcast_all")],
        [InlineKeyboardButton(text="🎯 Рассылка урок 1+", callback_data="admin_broadcast_l1")],
        [InlineKeyboardButton(text="🎯 Рассылка урок 2+", callback_data="admin_broadcast_l2")],
        [InlineKeyboardButton(text="🎯 Рассылка урок 3+", callback_data="admin_broadcast_l3")],
    ])

def crm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Горячие", callback_data="crm_hot")],
        [InlineKeyboardButton(text="🌤 Тёплые", callback_data="crm_warm")],
        [InlineKeyboardButton(text="❄️ Холодные", callback_data="crm_cold")],
        [InlineKeyboardButton(text="💰 Готовы купить", callback_data="crm_ready")],
        [InlineKeyboardButton(text="📞 Перезвонить", callback_data="crm_callback")],
        [InlineKeyboardButton(text="📁 Экспорт CRM", callback_data="crm_export")],
    ])

def calc_unit_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🧮 Рассчитать юнит-экономику", callback_data="unit_calc_start")]])

def unit_api_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить API-ключ", callback_data="unit_update_api")],
        [InlineKeyboardButton(text="🗑 Удалить API-ключ", callback_data="unit_delete_api")],
        [InlineKeyboardButton(text="🧮 Новый расчёт", callback_data="unit_start")]
    ])

def product_choose_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Показать мои товары", callback_data="show_wb_products")],
        [InlineKeyboardButton(text="🔗 Ввести ссылку WB", callback_data="enter_wb_link")],
        [InlineKeyboardButton(text="🔢 Ввести SKU вручную", callback_data="enter_wb_sku")],
    ])

def work_model_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="FBO", callback_data="work_fbo"), InlineKeyboardButton(text="FBS", callback_data="work_fbs")]])
def fbo_shipment_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Короба", callback_data="fbo_ship_boxes")],
        [InlineKeyboardButton(text="🧱 Монопаллеты", callback_data="fbo_ship_monopallets")],
    ])
def warehouse_keyboard(page=0, per_page=5):
    total=len(FBO_WAREHOUSES); total_pages=max(1, math.ceil(total/per_page)); page=max(0,min(page,total_pages-1))
    buttons=[]
    for i, w in enumerate(FBO_WAREHOUSES[page*per_page:page*per_page+per_page], start=page*per_page):
        buttons.append([InlineKeyboardButton(text=w, callback_data=f"warehouse_id_{i}")])
    nav=[]
    if page>0:
        nav += [InlineKeyboardButton(text="⏮", callback_data="warehouse_page_0"), InlineKeyboardButton(text="◀️", callback_data=f"warehouse_page_{page-1}")]
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="warehouse_page_current"))
    if page<total_pages-1:
        nav += [InlineKeyboardButton(text="▶️", callback_data=f"warehouse_page_{page+1}"), InlineKeyboardButton(text="⏭", callback_data=f"warehouse_page_{total_pages-1}")]
    buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="✍️ Написать склад вручную", callback_data="warehouse_other")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def products_keyboard(cards, page=0, per_page=10, batch_index=0, has_next_batch=False):
    total=len(cards); total_pages=max(1, math.ceil(total/per_page)); page=max(0,min(page,total_pages-1))
    buttons=[]
    for card in cards[page*per_page:page*per_page+per_page]:
        nm_id=card.get("nmID"); title=card.get("title","Без названия")
        buttons.append([InlineKeyboardButton(text=f"{title[:25]} | {nm_id}", callback_data=f"select_product_{nm_id}")])
    nav=[]
    if page>0:
        nav += [InlineKeyboardButton(text="⏮", callback_data="products_page_0"), InlineKeyboardButton(text="◀️", callback_data=f"products_page_{page-1}")]
    nav.append(InlineKeyboardButton(text=f"Стр. {page+1}/{total_pages}", callback_data="products_page_current"))
    if page<total_pages-1:
        nav += [InlineKeyboardButton(text="▶️", callback_data=f"products_page_{page+1}"), InlineKeyboardButton(text="⏭", callback_data=f"products_page_{total_pages-1}")]
    buttons.append(nav)
    batch=[]
    if batch_index>0: batch.append(InlineKeyboardButton(text="⬅️ Прошлые 100", callback_data="products_batch_prev"))
    if has_next_batch: batch.append(InlineKeyboardButton(text="Следующие 100 ➡️", callback_data="products_batch_next"))
    if batch: buttons.append(batch)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
