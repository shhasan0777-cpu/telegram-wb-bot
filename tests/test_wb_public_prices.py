from app.services.wb_public_prices import parse_public_price


def test_parse_public_price_from_size_price_format():
    payload = {
        "data": {
            "products": [
                {
                    "id": 123,
                    "sizes": [
                        {
                            "price": {
                                "basic": 150000,
                                "product": 100000,
                                "total": 85000,
                            }
                        }
                    ],
                }
            ]
        }
    }

    result = parse_public_price("123", payload)

    assert result is not None
    assert result.basic_price == 1500
    assert result.price_after_sale == 1000
    assert result.final_price == 850
    assert result.spp_rub == 150
    assert result.spp_percent == 15


def test_parse_public_price_from_classic_price_u_format():
    payload = {
        "data": {
            "products": [
                {
                    "id": 123,
                    "priceU": 200000,
                    "salePriceU": 120000,
                    "sale": 25,
                    "sizes": [],
                }
            ]
        }
    }

    result = parse_public_price("123", payload)

    assert result is not None
    assert result.basic_price == 2000
    assert result.price_after_sale == 1500
    assert result.final_price == 1200
    assert result.spp_rub == 300
    assert result.spp_percent == 20


def test_parse_public_price_returns_none_for_missing_product_when_multiple_products():
    payload = {
        "data": {
            "products": [
                {
                    "id": 999,
                    "priceU": 200000,
                    "salePriceU": 120000,
                    "sale": 25,
                },
                {
                    "id": 888,
                    "priceU": 300000,
                    "salePriceU": 150000,
                    "sale": 30,
                },
            ]
        }
    }

    result = parse_public_price("123", payload)

    assert result is None
    
def test_parse_public_price_uses_single_product_as_fallback():
    payload = {
        "data": {
            "products": [
                {
                    "id": 999,
                    "priceU": 200000,
                    "salePriceU": 120000,
                    "sale": 25,
                }
            ]
        }
    }

    result = parse_public_price("123", payload)

    assert result is not None
    assert result.final_price == 1200
    assert result.price_after_sale == 1500
    assert result.spp_percent == 20