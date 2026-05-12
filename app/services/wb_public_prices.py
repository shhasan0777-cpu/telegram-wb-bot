import aiohttp
from dataclasses import dataclass


WB_PUBLIC_CARD_URL = "https://card.wb.ru/cards/v2/detail"
WB_BASKET_HOSTS = [
    "basket-01.wbbasket.ru",
    "basket-02.wbbasket.ru",
    "basket-03.wbbasket.ru",
    "basket-04.wbbasket.ru",
    "basket-05.wbbasket.ru",
    "basket-06.wbbasket.ru",
    "basket-07.wbbasket.ru",
    "basket-08.wbbasket.ru",
    "basket-09.wbbasket.ru",
    "basket-10.wbbasket.ru",
    "basket-11.wbbasket.ru",
    "basket-12.wbbasket.ru",
    "basket-13.wbbasket.ru",
    "basket-14.wbbasket.ru",
    "basket-15.wbbasket.ru",
]
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

        final_price = (
            _money_from_wb(price.get("total"))
            or _money_from_wb(price.get("salePriceU"))
            or _money_from_wb(size.get("salePriceU"))
        )

        price_after_sale = (
            _money_from_wb(price.get("product"))
            or _money_from_wb(price.get("priceWithSale"))
            or _money_from_wb(size.get("priceWithSale"))
        )

        basic_price = (
            _money_from_wb(price.get("basic"))
            or _money_from_wb(price.get("priceU"))
            or _money_from_wb(size.get("priceU"))
        )
        
        if not final_price:
            continue

        if not price_after_sale:
            sale_percent = product.get("sale") or 0
            if basic_price and sale_percent:
                price_after_sale = round(basic_price * (1 - float(sale_percent) / 100), 2)
            else:
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

    if not products:
        return None

    matched_product = None

    for product in products:
        product_id = str(
            product.get("id")
            or product.get("nmID")
            or product.get("nmId")
            or product.get("root")
            or ""
        )

        if product_id == str(nm_id):
            matched_product = product
            break

    # Если WB вернул один товар по конкретному nm,
    # берём его даже если id лежит не в ожидаемом поле.
    if matched_product is None and len(products) == 1:
        matched_product = products[0]

    if matched_product is None:
        return None

    price = _extract_price_from_size(nm_id, matched_product, source_url)
    if price:
        return price

    return _extract_price_from_product(nm_id, matched_product, source_url)
def build_basket_urls(nm_id: str) -> list[str]:
    nm = int(nm_id)
    vol = nm // 100000
    part = nm // 1000

    urls = []

    for host in WB_BASKET_HOSTS:
        urls.append(
            f"https://{host}/vol{vol}/part{part}/{nm}/info/ru/card.json"
        )

    return urls

async def get_public_price(nm_id: str, dest: int = DEFAULT_DEST) -> WBPublicPrice | None:
    print("GET_PUBLIC_PRICE CALLED:", nm_id)

    nm_id = str(nm_id).strip()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx",
    }

    timeout = aiohttp.ClientTimeout(total=15, connect=5)

    # 1. Сначала пробуем card.wb.ru
    params = {
        "appType": "1",
        "curr": "rub",
        "dest": str(dest),
        "spp": "30",
        "ab_testing": "false",
        "lang": "ru",
        "nm": nm_id,
    }

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(WB_PUBLIC_CARD_URL, headers=headers, params=params) as response:
                text = await response.text()

                print("WB PUBLIC URL:", str(response.url))
                print("WB PUBLIC STATUS:", response.status)
                print("WB PUBLIC TEXT:", text[:1000])

                if response.status == 200:
                    payload = await response.json(content_type=None)
                    parsed = parse_public_price(nm_id, payload, source_url=str(response.url))
                    if parsed:
                        return parsed

            # 2. Если card.wb.ru дал 403, пробуем basket hosts
            for url in build_basket_urls(nm_id):
                try:
                    async with session.get(url, headers=headers) as response:
                        text = await response.text()

                        print("WB BASKET URL:", str(response.url))
                        print("WB BASKET STATUS:", response.status)
                        print("WB BASKET TEXT:", text[:1000])

                        if response.status != 200:
                            continue

                        payload = await response.json(content_type=None)

                        # basket card.json обычно не содержит СПП-цену.
                        # Но может содержать базовые данные карточки.
                        # Поэтому пока используем его только как диагностику.
                        print("WB BASKET PAYLOAD:", payload)

                        return None

                except Exception as e:
                    print("WB BASKET ERROR:", url, repr(e))
                    continue

    except Exception as e:
        print("WB PUBLIC ERROR:", repr(e))
        return None

    return None