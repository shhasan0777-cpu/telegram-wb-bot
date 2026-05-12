import html, math
from aiogram.exceptions import TelegramBadRequest
from app.keyboards.common import calc_unit_keyboard
from app.services.economics import calc_volume_liters
from app.services.wb_client import WBClient
from app.services.wb_public_prices import get_public_price


def get_card_photo(card):
    photos=card.get("photos") or []
    return (photos[0].get("big") or photos[0].get("c516x688") or photos[0].get("tm")) if photos else None

def get_card_barcode(card):
    for size in card.get("sizes") or []:
        skus=size.get("skus") or []
        if skus: return skus[0]
    return None

def get_card_size(card):
    vals=[]
    for size in card.get("sizes") or []:
        value=size.get("techSize") or size.get("wbSize")
        if value and value not in ["0",""]: vals.append(str(value))
    return ", ".join(vals[:5]) if vals else None

def money_to_float(value):
    try: return float(str(value).replace(",","."))
    except Exception: return 0

def find_warehouse_tariff(tariffs, warehouse_name):
    if not tariffs or not warehouse_name: return None
    wh=warehouse_name.lower()
    for item in tariffs:
        name=(item.get("warehouseName") or "").lower()
        if wh in name or name in wh: return item
    return None

def calc_logistics_by_tariff(tariff, billing_liters):
    if not tariff: return 0
    first=money_to_float(tariff.get("boxDeliveryBase")); nxt=money_to_float(tariff.get("boxDeliveryLiter"))
    return first if billing_liters<=1 else first+(billing_liters-1)*nxt

def calc_commission(price, percent):
    try: return float(price)*float(percent)/100
    except Exception: return 0

async def build_product_data(api_key, selected_card, nm_id):
    dimensions=selected_card.get("dimensions",{})
    volume_liters,billing_liters=calc_volume_liters(dimensions.get("length"), dimensions.get("width"), dimensions.get("height"))
    client=WBClient(api_key)
    prices=await client.get_prices(nm_id)
    seller_price=promo_price=None
    for item in prices:
        item_nm=str(item.get("nmID") or item.get("nmId") or item.get("nm") or "")
        if item_nm != str(nm_id): continue
        all_prices=[]
        for size in item.get("sizes") or []:
            for key in ["price","discountedPrice","clubDiscountedPrice","priceWithDisc","discountedPriceWithClub"]:
                value=size.get(key)
                if value not in (None,"",0): all_prices.append(float(value))
        if all_prices:
            seller_price=max(all_prices); promo_price=min(all_prices)
        break
    public_price = await get_public_price(nm_id)

    wb_price = public_price.final_price if public_price else None
    price_after_sale = public_price.price_after_sale if public_price else None
    spp_percent = public_price.spp_percent if public_price else 0
    spp_rub = public_price.spp_rub if public_price else 0
    commissions=await client.get_commissions()
    commission_percent=0; subject=(selected_card.get("subjectName") or "").lower()
    for item in commissions:
        if (item.get("subjectName") or "").lower()==subject:
            commission_percent=item.get("kgvpMarketplace") or 0; break
    price_for_calc = wb_price or promo_price or seller_price or 0
    return {
        "nm_id": nm_id,
        "product_name": selected_card.get("title"),
        "vendor_code": selected_card.get("vendorCode"),
        "brand": selected_card.get("brand"),
        "category": selected_card.get("subjectName"),
        "barcode": get_card_barcode(selected_card),
        "size": get_card_size(selected_card),
        "photo": get_card_photo(selected_card),

        "seller_price": seller_price,
        "promo_price": promo_price,
        "wb_price": wb_price,

        "price": seller_price,
        "price_after_sale": price_after_sale,
        "price_with_spp": price_for_calc,

        "spp_percent": spp_percent,
        "spp_rub": spp_rub,
        "public_price_source": public_price.source_url if public_price else None,

        "commission_percent": commission_percent,
        "commission_rub": calc_commission(price_for_calc, commission_percent),

        "width": dimensions.get("width"),
        "height": dimensions.get("height"),
        "length": dimensions.get("length"),
        "weight": selected_card.get("weightBrutto"),
        "volume_liters": volume_liters,
        "billing_liters": billing_liters,
    }
    
def build_product_preview_text(data):
    name=html.escape(str(data.get("product_name") or "Товар")); nm_id=data.get("nm_id")
    vendor=html.escape(str(data.get("vendor_code") or "не указан")); brand=html.escape(str(data.get("brand") or "не указан")); category=html.escape(str(data.get("category") or "не указана")); barcode=html.escape(str(data.get("barcode") or "не указан"))
    product_url=f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx"
    text=(f"📦 <a href=\"{product_url}\">{name}</a>\n\nАртикул WB: <b>{nm_id}</b>\nАртикул продавца: <b>{vendor}</b>\nЦена продавца: <b>{data.get('seller_price') or 'не найдена'} ₽</b>\nЦена по акции: <b>{data.get('promo_price') or 'не найдена'} ₽</b>\nЦена на WB: <b>{data.get('wb_price') or 'не найдена'} ₽</b>\nСкидка СПП: <b>{data.get('spp_percent') or 0}%</b>\nКатегория: <b>{category}</b>\nБренд: <b>{brand}</b>\n")
    if data.get("size"): text += f"Размер: <b>{html.escape(str(data.get('size')))}</b>\n"
    return text + f"Баркод: <b>{barcode}</b>"

async def send_product_preview(message, data):
    text=build_product_preview_text(data)
    if data.get("photo"):
        try:
            await message.answer_photo(photo=data["photo"], caption=text, parse_mode="HTML", reply_markup=calc_unit_keyboard()); return
        except TelegramBadRequest:
            pass
    await message.answer(text, parse_mode="HTML", reply_markup=calc_unit_keyboard(), disable_web_page_preview=True)
