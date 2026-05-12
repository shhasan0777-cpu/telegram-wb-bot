from app.services.validation import parse_non_negative_float


def test_parse_accepts_comma():
    assert parse_non_negative_float("12,5") == 12.5


def test_parse_rejects_negative():
    assert parse_non_negative_float("-1") is None


def test_parse_rejects_too_big():
    assert parse_non_negative_float("101", max_value=100) is None
