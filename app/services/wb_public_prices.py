import aiohttp
from dataclasses import dataclass


WB_PUBLIC_CARD_URL = "https://card.wb.ru/cards/v2/detail"
DEFAULT_DEST = -1257786


@dataclass(frozen=True)
class WBPublicPrice:
    nm_id: str
    final_price: float
    price_after_sale: float
    basic_price: float | None
    sale_percent: float | None
    spp_percent: float
    spp_rub: float
    source_url: str


def _money_from_wb(value) -> float | None:
    """
    WB часто отдаёт цены в копейках: 123456 => 1234.56.
    Иногда в новых структурах может прийти уже нормальная цена.
    """
    if value in (None, "", 0):
        return None

    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None

    if amount > 10000:
        amount = amount / 100

    return round(amount, 2)


def _calc_spp(final_price: float, price_after_sale: float) -> tuple[float, float]:
    if not final_price or not price_after_sale or price_after_sale <= 0:
        return 0.0, 0.0

    spp_rub = max(price_after_sale - final_price, 0)
    spp_percent = (1 - final_price / price_after_sale) * 100

    return round(spp_percent, 2), round(spp_rub, 2)


def _extract_price_from_size(nm_id: str, product: dict, source_url: str) -> WBPublicPrice | None:
    """
    Новый формат WB:
    product["sizes"][...]["price"]["basic"]
    product["sizes"][...]["price"]["product"]
    product["sizes"][...]["price"]["total"]

    basic   — базовая/зачёркнутая цена
    product — цена после скидки продавца
    total   — финальная цена покупателя с СПП
    """
    sizes = product.get("sizes") or []

    candidates: list[WBPublicPrice] = []

    for size in sizes:
        price = size.get("price") or {}

        final_price = _money_from_wb(price.get("total"))
        price_after_sale = _money_from_wb(price.get("product"))
        basic_price = _money_from_wb(price.get("basic"))

        if not final_price:
            continue

        if not price_after_sale:
            price_after_sale = final_price

        spp_percent, spp_rub = _calc_spp(final_price, price_after_sale)

        candidates.append(
            WBPublicPrice(
                nm_id=str(nm_id),
                final_price=final_price,
                price_after_sale=price_after_sale,
                basic_price=basic_price,
                sale_percent=None,
                spp_percent=spp_percent,
                spp_rub=spp_rub,
                source_url=source_url,
            )
        )

    if not candidates:
        return None

    return min(candidates, key=lambda item: item.final_price)


def _extract_price_from_product(nm_id: str, product: dict, source_url: str) -> WBPublicPrice | None:
    """
    Старый/классический формат WB:
    priceU
    salePriceU
    sale
    """
    final_price = _money_from_wb(product.get("salePriceU"))
    basic_price = _money_from_wb(product.get("priceU"))

    if not final_price:
        return None

    sale_percent = product.get("sale") or 0

    if basic_price:
        price_after_sale = basic_price * (1 - float(sale_percent) / 100)
        price_after_sale = round(price_after_sale, 2)
    else:
        price_after_sale = final_price

    spp_percent, spp_rub = _calc_spp(final_price, price_after_sale)

    return WBPublicPrice(
        nm_id=str(nm_id),
        final_price=final_price,
        price_after_sale=price_after_sale,
        basic_price=basic_price,
        sale_percent=float(sale_percent or 0),
        spp_percent=spp_percent,
        spp_rub=spp_rub,
        source_url=source_url,
    )


def parse_public_price(nm_id: str, payload: dict, source_url: str = WB_PUBLIC_CARD_URL) -> WBPublicPrice | None:
    products = payload.get("data", {}).get("products", [])

    for product in products:
        if str(product.get("id") or product.get("nmID") or product.get("nmId") or "") != str(nm_id):
            continue

        price = _extract_price_from_size(nm_id, product, source_url)
        if price:
            return price

        return _extract_price_from_product(nm_id, product, source_url)

    return None


async def get_public_price(nm_id: str, dest: int = DEFAULT_DEST) -> WBPublicPrice | None:
    nm_id = str(nm_id).strip()

    params = {
        "appType": 1,
        "curr": "rub",
        "dest": dest,
        "nm": nm_id,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx",
    }

    timeout = aiohttp.ClientTimeout(total=15, connect=5)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(WB_PUBLIC_CARD_URL, headers=headers, params=params) as response:
            if response.status != 200:
                return None

            payload = await response.json(content_type=None)
            print("WB PUBLIC STATUS:", response.status)
            print("WB PUBLIC PAYLOAD:", payload)

    source_url = (
        f"{WB_PUBLIC_CARD_URL}"
        f"?appType=1&curr=rub&dest={dest}&nm={nm_id}"
    )

    return parse_public_price(nm_id, payload, source_url=source_url)