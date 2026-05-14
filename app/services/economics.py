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

def calc_fbo_logistics_full(
    billing_liters,
    price_for_calc,
    warehouse_coeff=1,
    logistics_index=1,
    irp_percent=0,
    base_first_liter=46,
    extra_liter_price=14,
):
    try:
        billing_liters = float(billing_liters or 0)
        price_for_calc = float(price_for_calc or 0)
        warehouse_coeff = float(warehouse_coeff or 1)
        logistics_index = float(logistics_index or 1)
        irp_percent = float(irp_percent or 0)
        base_first_liter = float(base_first_liter or 46)
        extra_liter_price = float(extra_liter_price or 14)

        extra_liters = max(billing_liters - 1, 0)
        base_logistics = base_first_liter + extra_liters * extra_liter_price

        result = (
            base_logistics
            * warehouse_coeff
            * logistics_index
            + price_for_calc * irp_percent / 100
        )

        return {
            "base_first_liter": round(base_first_liter, 2),
            "extra_liter_price": round(extra_liter_price, 2),
            "base_logistics": round(base_logistics, 2),
            "warehouse_coeff": round(warehouse_coeff, 4),
            "logistics_index": round(logistics_index, 4),
            "irp_percent": round(irp_percent, 2),
            "logistics_rub": round(result, 2),
        }
    except Exception:
        return {
            "base_first_liter": 46,
            "extra_liter_price": 14,
            "base_logistics": 0,
            "warehouse_coeff": 1,
            "logistics_index": 1,
            "irp_percent": 0,
            "logistics_rub": 0,
        }
    
def calc_volume_liters(length, width, height):
    try:
        volume = float(length) * float(width) * float(height) / 1000
        return volume, math.ceil(volume)
    except Exception:
        return 0, 0
def calc_wb_fbo_logistics(
    billing_liters: float,
    product_price: float,
    warehouse_coeff: float = 1,
    logistics_index: float = 1,
    irp_percent: float = 0,
    base_liter_price: float = 46,
    extra_liter_price: float = 14,
) -> float:
    """
    Расчёт FBO-логистики WB:

    (46 ₽ за 1 л + 14 ₽ за каждый доп. литр)
    × коэффициент склада
    × ИЛ в день заказа
    + цена товара × ИРП в день заказа
    """
    try:
        liters = max(float(billing_liters or 0), 1)
        price = float(product_price or 0)
        coeff = float(warehouse_coeff or 1)
        il = float(logistics_index or 1)
        irp = float(irp_percent or 0)

        extra_liters = max(liters - 1, 0)
        logistics_part = (base_liter_price + extra_liter_price * extra_liters) * coeff * il
        irp_part = price * irp / 100

        return round(logistics_part + irp_part, 2)
    except Exception:
        return 0

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
