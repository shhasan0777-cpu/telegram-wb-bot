import aiohttp
import logging
from datetime import datetime

log = logging.getLogger(__name__)

class WBClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def _request(self, method: str, url: str, **kwargs):
        timeout = aiohttp.ClientTimeout(total=20, connect=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method, url, **kwargs) as response:
                text = await response.text()
                if response.status == 429:
                    raise RuntimeError("WB временно ограничил запросы. Подожди 1–2 минуты и попробуй снова.")
                if response.status >= 400:
                    raise RuntimeError(f"WB API ошибка: {response.status} — {text[:500]}")
                return await response.json(content_type=None)

    async def get_products(self, limit: int = 100, cursor: dict | None = None):
        url = "https://content-api.wildberries.ru/content/v2/get/cards/list"
        wb_cursor = {"limit": limit}
        if cursor:
            wb_cursor.update(cursor)
        data = await self._request("POST", url, headers={"Authorization": self.api_key, "Content-Type": "application/json"}, json={"settings": {"cursor": wb_cursor, "filter": {"withPhoto": -1}}})
        cards = data.get("cards", [])
        cursor_data = data.get("cursor", {})
        next_cursor = None
        if cards and cursor_data.get("updatedAt") and cursor_data.get("nmID") and len(cards) >= limit:
            next_cursor = {"updatedAt": cursor_data.get("updatedAt"), "nmID": cursor_data.get("nmID")}
        return cards, next_cursor

    async def get_prices(self, nm_id: str):
        url = "https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter"
        data = await self._request("GET", url, headers={"Authorization": self.api_key}, params={"limit": 1, "filterNmID": nm_id})
        return data.get("data", {}).get("listGoods", [])

    async def get_commissions(self):
        data = await self._request("GET", "https://common-api.wildberries.ru/api/v1/tariffs/commission", headers={"Authorization": self.api_key})
        return data.get("report", [])

    async def get_box_tariffs(self):
        today = datetime.now().strftime("%Y-%m-%d")
        data = await self._request("GET", "https://common-api.wildberries.ru/api/v1/tariffs/box", headers={"Authorization": self.api_key}, params={"date": today})
        return data.get("response", {}).get("data", {}).get("warehouseList", [])

async def wb_get_public_price(nm_id: str):
    url = "https://card.wb.ru/cards/v2/detail"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*", "Referer": f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx"}
    params = {"appType": 1, "curr": "rub", "dest": -446116, "spp": 30, "ab_testing": "false", "nm": str(nm_id).strip()}
    timeout = aiohttp.ClientTimeout(total=15, connect=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                return None
            data = await response.json(content_type=None)
    products = data.get("data", {}).get("products", [])
    prices = []
    for product in products:
        for size in product.get("sizes", []):
            price_data = size.get("price") or {}
            for key in ["total", "product", "basic"]:
                value = price_data.get(key)
                if value:
                    value = float(value)
                    if value > 10000:
                        value /= 100
                    prices.append(value)
    return min(prices) if prices else None
