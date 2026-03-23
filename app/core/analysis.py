import re

RANGE_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:-|to|–|—)\s*(-?\d+(?:\.\d+)?)")


def parse_range_string(range_text: str) -> tuple[float, float] | None:
    if not range_text:
        return None
    match = RANGE_PATTERN.search(range_text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def format_range(minimum: float, maximum: float) -> str:
    return f"{minimum} - {maximum}"


def classify_value(value: float, minimum: float, maximum: float) -> str:
    if minimum <= value <= maximum:
        return "NORMAL"

    if value < minimum:
        denominator = abs(minimum) if abs(minimum) > 1e-6 else 1.0
        deviation = (minimum - value) / denominator
        return "CRITICAL" if deviation >= 0.30 else "LOW"

    denominator = abs(maximum) if abs(maximum) > 1e-6 else 1.0
    deviation = (value - maximum) / denominator
    return "CRITICAL" if deviation >= 0.30 else "HIGH"

