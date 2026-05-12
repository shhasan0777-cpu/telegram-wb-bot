import math
from dataclasses import dataclass

@dataclass(frozen=True)
class UnitEconomicsInput:
    price_with_spp: float
    price: float
    commission_rub: float
    logistics_rub: float
    purchase_price: float
    fulfilment_price: float
    tax_percent: float
    other_expenses: float
    salary_expenses: float


def calc_volume_liters(length, width, height):
    try:
        volume = float(length) * float(width) * float(height) / 1000
        return volume, math.ceil(volume)
    except Exception:
        return 0, 0


def calc_unit_economics(data: UnitEconomicsInput) -> dict:
    tax_base = data.price_with_spp or data.price or 0
    tax_rub = tax_base * data.tax_percent / 100
    total_costs = (
        data.purchase_price + data.fulfilment_price + data.commission_rub +
        data.logistics_rub + tax_rub + data.other_expenses + data.salary_expenses
    )
    profit = data.price_with_spp - total_costs
    margin = (profit / data.price_with_spp * 100) if data.price_with_spp else 0
    roi = (profit / data.purchase_price * 100) if data.purchase_price else 0
    return {"tax_rub": round(tax_rub, 2), "total_costs": round(total_costs, 2), "profit": round(profit, 2), "margin": round(margin, 2), "roi": round(roi, 2)}
