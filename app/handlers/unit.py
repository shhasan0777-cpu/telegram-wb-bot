import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.repositories.unit_sessions import create_session, get_last_session, update_session, get_session_api_key
from app.repositories.products_cache import save_cache, get_cache
from app.repositories.users import save_user
from app.services.validation import parse_non_negative_float
from app.services.wb_client import WBClient
from app.services.products import build_product_data, send_product_preview, find_warehouse_tariff, calc_logistics_by_tariff
from app.services.economics import UnitEconomicsInput, calc_unit_economics, calc_volume_liters
from app.keyboards.common import product_choose_keyboard, products_keyboard, work_model_keyboard, warehouse_keyboard, unit_api_keyboard
from app.data.wb import FBO_WAREHOUSES

router = Router()

async def check_api_key(api_key: str):
    api_key=str(api_key).strip()
    if len(api_key)<50: return False, "Ключ слишком короткий."
    if not api_key.isascii(): return False, "API-ключ должен содержать только латинские символы, цифры и спецсимволы."
    if any(ch.isspace() for ch in api_key): return False, "API-ключ не должен содержать пробелы или переносы строк."
    try:
        await WBClient(api_key).get_products(limit=1)
        return True, None
    except Exception as e:
        return False, str(e)

@router.callback_query(F.data == "unit_start")
async def unit_start(callback: CallbackQuery):
    save_user(callback.from_user.id, callback.from_user.username)
    create_session(callback.from_user.id, "api_key")
    await callback.message.answer("🧮 Начинаем расчёт юнит-экономики WB.\n\nОтправь API-ключ Wildberries.\n\nНужные доступы:\n• Контент\n• Цены и скидки\n• Аналитика / Статистика\n• Финансы\n• Продвижение\n• Возвраты\n• Поставки")
    await callback.answer()

@router.callback_query(F.data == "unit_update_api")
async def unit_update_api(callback: CallbackQuery):
    create_session(callback.from_user.id, "api_key")
    await callback.message.answer("🔄 Отправь новый API-ключ WB:"); await callback.answer()

@router.callback_query(F.data == "unit_delete_api")
async def unit_delete_api(callback: CallbackQuery):
    session=get_last_session(callback.from_user.id)
    if session: update_session(session["id"], api_key=None, stage="api_key")
    await callback.message.answer("🗑 API-ключ удалён.\n\nЧтобы начать заново, нажми «Новый расчёт».", reply_markup=unit_api_keyboard()); await callback.answer()

@router.callback_query(F.data == "show_wb_products")
async def show_wb_products(callback: CallbackQuery):
    session=get_last_session(callback.from_user.id); api_key=get_session_api_key(session)
    if not session or not api_key: await callback.answer(); return
    await callback.message.answer("⏳ Загружаю первые 100 товаров из WB...")
    try: cards,next_cursor=await WBClient(api_key).get_products(100)
    except Exception as e:
        await callback.message.answer(f"❌ Не удалось получить товары.\n\n{e}\n\nПроверь API-ключ и доступ «Контент»."); await callback.answer(); return
    if not cards:
        await callback.message.answer("Товары не найдены.\n\nМожешь выбрать: 🔢 Ввести SKU вручную или 🔗 Ввести ссылку WB."); await callback.answer(); return
    save_cache(callback.from_user.id, {"batches":[{"cards":cards,"cursor":None,"next_cursor":next_cursor}],"batch_index":0})
    await callback.message.answer("📦 Выбери товар:", reply_markup=products_keyboard(cards,0,10,0,bool(next_cursor)))
    await callback.answer()

@router.callback_query(F.data.startswith("products_page_"))
async def products_page(callback: CallbackQuery):
    if callback.data == "products_page_current": await callback.answer(); return
    cache=get_cache(callback.from_user.id)
    if not cache: await callback.answer("Список товаров устарел. Нажми «Показать мои товары» заново."); return
    page=int(callback.data.replace("products_page_", "")); bi=cache["batch_index"]; batch=cache["batches"][bi]
    await callback.message.edit_reply_markup(reply_markup=products_keyboard(batch["cards"], page, 10, bi, bool(batch["next_cursor"])))
    await callback.answer()

@router.callback_query(F.data.in_(["products_batch_next","products_batch_prev"]))
async def products_batch(callback: CallbackQuery):
    session=get_last_session(callback.from_user.id); api_key=get_session_api_key(session); cache=get_cache(callback.from_user.id)
    if not session or not api_key or not cache: await callback.answer("Список товаров устарел. Нажми «Показать мои товары» заново."); return
    if callback.data=="products_batch_prev":
        if cache["batch_index"]<=0: await callback.answer("Ты уже в начале списка."); return
        cache["batch_index"]-=1; bi=cache["batch_index"]; batch=cache["batches"][bi]; save_cache(callback.from_user.id, cache)
        await callback.message.edit_text(f"📦 Товары {bi*100+1}–{bi*100+len(batch['cards'])}:", reply_markup=products_keyboard(batch["cards"],0,10,bi,bool(batch["next_cursor"])))
        await callback.answer(); return
    current=cache["batch_index"]; current_batch=cache["batches"][current]; next_cursor=current_batch["next_cursor"]
    if not next_cursor: await callback.answer("Больше товаров нет."); return
    next_index=current+1
    if next_index < len(cache["batches"]):
        cache["batch_index"]=next_index; save_cache(callback.from_user.id, cache); batch=cache["batches"][next_index]
        await callback.message.edit_text(f"📦 Товары {next_index*100+1}–{next_index*100+len(batch['cards'])}:", reply_markup=products_keyboard(batch["cards"],0,10,next_index,bool(batch["next_cursor"])))
        await callback.answer(); return
    await callback.message.edit_text("⏳ Загружаю следующие 100 товаров из WB...")
    try: cards,new_next=await WBClient(api_key).get_products(100,next_cursor)
    except Exception as e: await callback.message.edit_text(f"❌ Не удалось загрузить следующие товары.\n\n{e}"); await callback.answer(); return
    if not cards:
        current_batch["next_cursor"]=None; save_cache(callback.from_user.id, cache)
        await callback.message.edit_text("✅ Больше товаров нет.", reply_markup=products_keyboard(current_batch["cards"],0,10,current,False)); await callback.answer(); return
    cache["batches"].append({"cards":cards,"cursor":next_cursor,"next_cursor":new_next}); cache["batch_index"]=next_index; save_cache(callback.from_user.id, cache)
    await callback.message.edit_text(f"📦 Товары {next_index*100+1}–{next_index*100+len(cards)}:", reply_markup=products_keyboard(cards,0,10,next_index,bool(new_next)))
    await callback.answer()

@router.callback_query(F.data == "enter_wb_link")
async def enter_wb_link(callback: CallbackQuery):
    s=get_last_session(callback.from_user.id)
    if s: update_session(s["id"], stage="product_link"); await callback.message.answer("Отправь ссылку на товар Wildberries:")
    await callback.answer()

@router.callback_query(F.data == "enter_wb_sku")
async def enter_wb_sku(callback: CallbackQuery):
    s=get_last_session(callback.from_user.id)
    if s: update_session(s["id"], stage="product_sku"); await callback.message.answer("Отправь SKU / nmID товара или артикул продавца:")
    await callback.answer()

@router.callback_query(F.data.startswith("select_product_"))
async def select_product(callback: CallbackQuery):
    user_id=callback.from_user.id; nm_id=callback.data.replace("select_product_","")
    session=get_last_session(user_id); api_key=get_session_api_key(session); cache=get_cache(user_id)
    if not session or not api_key: await callback.answer(); return
    selected=None
    if cache:
        batch=cache["batches"][cache["batch_index"]]
        selected=next((c for c in batch["cards"] if str(c.get("nmID"))==str(nm_id)), None)
    if not selected:
        try: cards,_=await WBClient(api_key).get_products(100)
        except Exception as e: await callback.message.answer(str(e)); await callback.answer(); return
        selected=next((c for c in cards if str(c.get("nmID"))==str(nm_id)), None)
    if not selected: await callback.message.answer("❌ Товар не найден."); await callback.answer(); return
    data=await build_product_data(api_key, selected, nm_id)
    update_session(session["id"], stage="product_confirm", **{k:v for k,v in data.items() if k in ["nm_id","product_name","vendor_code","price","spp_percent","price_with_spp","commission_percent","commission_rub","width","height","length","weight"]})
    await send_product_preview(callback.message, data); await callback.answer()

@router.callback_query(F.data == "unit_calc_start")
async def unit_calc_start(callback: CallbackQuery):
    s=get_last_session(callback.from_user.id)
    if s: update_session(s["id"], stage="work_model"); await callback.message.answer("Теперь выбери модель работы:", reply_markup=work_model_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("work_"))
async def choose_work_model(callback: CallbackQuery):
    s=get_last_session(callback.from_user.id)
    if not s: await callback.answer(); return
    model=callback.data.replace("work_","").upper()
    if model=="FBO":
        update_session(s["id"], work_model=model, stage="warehouse_choose")
        await callback.message.answer("✅ Модель работы: FBO\n\nВыбери склад из списка или напиши название склада вручную 👇", reply_markup=warehouse_keyboard())
    else:
        update_session(s["id"], work_model=model, warehouse_name=None, stage="purchase_price")
        await callback.message.answer("✅ Модель работы: FBS\n\nВведите закупку товара за 1 шт в ₽:")
    await callback.answer()

@router.callback_query(F.data.startswith("warehouse_page_"))
async def warehouse_page(callback: CallbackQuery):
    if callback.data=="warehouse_page_current": await callback.answer(); return
    await callback.message.edit_reply_markup(reply_markup=warehouse_keyboard(int(callback.data.replace("warehouse_page_", ""))))
    await callback.answer()

@router.callback_query(F.data.startswith("warehouse_id_"))
async def choose_warehouse_by_id(callback: CallbackQuery):
    s=get_last_session(callback.from_user.id)
    if not s: await callback.answer(); return
    idx=int(callback.data.replace("warehouse_id_", ""))
    if idx<0 or idx>=len(FBO_WAREHOUSES): await callback.answer("Склад не найден"); return
    wh=FBO_WAREHOUSES[idx]; update_session(s["id"], warehouse_name=wh, stage="purchase_price")
    await callback.message.answer(f"✅ Склад: {wh}\n\nВведите закупку товара за 1 шт в ₽:"); await callback.answer()

@router.callback_query(F.data == "warehouse_other")
async def warehouse_other(callback: CallbackQuery):
    s=get_last_session(callback.from_user.id)
    if s: update_session(s["id"], stage="warehouse_text"); await callback.message.answer("Введи название склада текстом:")
    await callback.answer()

@router.message(F.text)
async def unit_text_handler(message: Message):
    if message.text.strip().startswith("/"): return
    session=get_last_session(message.from_user.id)
    if not session: return
    await handle_unit_stage(message, session, session["stage"], message.text.strip())

async def process_product_by_nm(message: Message, session, query: str):
    api_key=get_session_api_key(session); query=str(query).strip()
    await message.answer("⏳ Ищу товар в твоём кабинете WB...")
    try: cards,_=await WBClient(api_key).get_products(100)
    except Exception as e: await message.answer(f"❌ Не удалось получить данные товара.\n\n{e}"); return
    selected=None
    for card in cards:
        if query==str(card.get("nmID") or "").strip() or query.lower()==str(card.get("vendorCode") or "").strip().lower(): selected=card; break
    if not selected:
        await message.answer("❌ Товар не найден в твоём кабинете WB.\n\nМожно отправить:\n• SKU / nmID товара WB\n• артикул продавца\n\nПроверь значение и отправь ещё раз."); return
    data=await build_product_data(api_key, selected, selected.get("nmID"))
    update_session(session["id"], stage="product_confirm", **{k:v for k,v in data.items() if k in ["nm_id","product_name","vendor_code","price","spp_percent","price_with_spp","commission_percent","commission_rub","width","height","length","weight"]})
    await send_product_preview(message, data)

async def handle_unit_stage(message: Message, session, stage: str, text: str):
    uid=message.from_user.id
    if stage=="api_key":
        await message.answer("⏳ Проверяю API-ключ WB...")
        ok,err=await check_api_key(text)
        if not ok: await message.answer(f"❌ API-ключ не прошёл проверку.\n\nПричина: {err}\n\nПроверь, что ты отправил именно API-ключ Wildberries."); return
        update_session(session["id"], api_key=text, stage="product_choose")
        await message.answer("✅ API-ключ проверен и сохранён.\n\nТеперь выбери товар для расчёта:", reply_markup=product_choose_keyboard()); return
    if stage=="product_link":
        m=re.search(r"/catalog/(\d+)/", text)
        if not m: await message.answer("❌ Не смог найти SKU в ссылке.\n\nПришли ссылку вида:\nhttps://www.wildberries.ru/catalog/123456789/detail.aspx"); return
        await process_product_by_nm(message, session, m.group(1)); return
    if stage=="product_sku": await process_product_by_nm(message, session, text); return
    if stage=="warehouse_text": update_session(session["id"], warehouse_name=text, stage="purchase_price"); await message.answer(f"✅ Склад: {text}\n\nВведите закупку товара за 1 шт в ₽:"); return
    prompts={"purchase_price":("purchase_price","fulfilment_price","Введите фулфилмент за 1 шт в ₽:"),"fulfilment_price":("fulfilment_price","tax_percent","Введите налог в %:\n\nПример: 6 (для УСН) или 0"),"tax_percent":("tax_percent","other_expenses","Введите прочие расходы в ₽ (упаковка, этикетки и т.д.):\n\nЕсли нет — введите 0"),"other_expenses":("other_expenses","salary_expenses","Введите расходы на зарплаты в ₽:\n\nЕсли нет — введите 0")}
    if stage in prompts:
        val=parse_non_negative_float(text, max_value=100 if stage=="tax_percent" else None)
        if val is None: await message.answer("Введите неотрицательное число." if stage!="tax_percent" else "Введите налог от 0 до 100."); return
        col,next_stage,prompt=prompts[stage]; update_session(session["id"], **{col:val,"stage":next_stage}); await message.answer(prompt); return
    if stage=="salary_expenses":
        val=parse_non_negative_float(text)
        if val is None: await message.answer("Введите неотрицательное число."); return
        update_session(session["id"], salary_expenses=val); updated=get_last_session(uid); api_key=get_session_api_key(updated)
        logistics=0
        if updated["work_model"]=="FBO":
            tariffs=await WBClient(api_key).get_box_tariffs(); _, billing=calc_volume_liters(updated["length"],updated["width"],updated["height"])
            logistics=calc_logistics_by_tariff(find_warehouse_tariff(tariffs, updated["warehouse_name"]), billing)
            update_session(updated["id"], logistics_rub=logistics); updated=get_last_session(uid)
        result=calc_unit_economics(UnitEconomicsInput(price_with_spp=updated["price_with_spp"] or 0, price=updated["price"] or 0, commission_rub=updated["commission_rub"] or 0, logistics_rub=updated["logistics_rub"] or 0, purchase_price=updated["purchase_price"] or 0, fulfilment_price=updated["fulfilment_price"] or 0, tax_percent=updated["tax_percent"] or 0, other_expenses=updated["other_expenses"] or 0, salary_expenses=updated["salary_expenses"] or 0))
        volume,billing=calc_volume_liters(updated["length"],updated["width"],updated["height"])
        update_session(updated["id"], profit_per_unit=result["profit"], margin_percent=result["margin"], roi_percent=result["roi"], stage="completed")
        emoji="✅" if result["profit"]>0 else "❌"
        await message.answer(f"🧮 Юнит-экономика WB\n\n📦 Товар: {updated['product_name'] or updated['nm_id']}\nМодель: {updated['work_model']}\nСклад: {updated['warehouse_name'] or 'FBS'}\n\n━━━━━━━━━━━━━━━━\n💰 Цена покупателя: {round(updated['price_with_spp'] or 0, 2)} ₽\n🏷 Комиссия WB: {updated['commission_percent']}% = {round(updated['commission_rub'] or 0, 2)} ₽\n🚚 Логистика WB: {round(updated['logistics_rub'] or 0, 2)} ₽\n📦 Литраж: {round(volume, 2)} л (расч. {billing} л)\n\n━━━━━━━━━━━━━━━━\n🛒 Закупка: {updated['purchase_price']} ₽\n🏭 Фулфилмент: {updated['fulfilment_price']} ₽\n📊 Налог: {updated['tax_percent']}% = {result['tax_rub']} ₽\n📌 Прочие расходы: {updated['other_expenses']} ₽\n👥 Зарплаты: {updated['salary_expenses']} ₽\n\n━━━━━━━━━━━━━━━━\n💼 Все расходы: {result['total_costs']} ₽\n\n{emoji} Прибыль с 1 шт: {result['profit']} ₽\n📈 Маржа: {result['margin']}%\n💹 ROI: {result['roi']}%", reply_markup=unit_api_keyboard())
