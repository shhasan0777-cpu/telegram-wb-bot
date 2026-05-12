def parse_non_negative_float(value: str, *, max_value: float | None = None) -> float | None:
    try:
        result = float(str(value).replace(",", ".").strip())
    except Exception:
        return None
    if result < 0:
        return None
    if max_value is not None and result > max_value:
        return None
    return result
