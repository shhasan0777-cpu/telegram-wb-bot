from app.services.economics import UnitEconomicsInput, calc_unit_economics, calc_volume_liters


def test_calc_volume_liters_rounds_billing_volume_up():
    assert calc_volume_liters(10, 10, 11) == (1.1, 2)


def test_calc_unit_economics_profit_margin_roi():
    result = calc_unit_economics(UnitEconomicsInput(price_with_spp=1000, price=1200, commission_rub=100, logistics_rub=50, purchase_price=300, fulfilment_price=40, tax_percent=6, other_expenses=20, salary_expenses=30))
    assert result["tax_rub"] == 60
    assert result["total_costs"] == 600
    assert result["profit"] == 400
    assert result["margin"] == 40
    assert round(result["roi"], 2) == 133.33
