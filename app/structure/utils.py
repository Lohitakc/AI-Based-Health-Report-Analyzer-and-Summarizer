from __future__ import annotations

import re
from typing import Iterable

VALUE_PATTERN = re.compile(r"(?<![A-Za-z])(-?\d+(?:\.\d+)?)(?![A-Za-z])")
RANGE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)")
MICRO = "\u00b5"
UNIT_PATTERN = re.compile(
    rf"(mg/dl|gm/dl|g/dl|u/l|/cmm|/hpf|%|ng/dl|ug/dl|{MICRO}g/dl|uiu/ml|{MICRO}iu/ml)",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    text = text.replace("\t", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def extract_ranges(line: str) -> list[tuple[float, float]]:
    ranges: list[tuple[float, float]] = []
    for match in RANGE_PATTERN.finditer(line):
        minimum = float(match.group(1))
        maximum = float(match.group(2))
        ranges.append((minimum, maximum))
    return ranges


def extract_value(line: str) -> float | None:
    value_matches = list(VALUE_PATTERN.finditer(line))
    if not value_matches:
        return None

    range_match = RANGE_PATTERN.search(line)
    if range_match:
        candidate_values = [match for match in value_matches if match.start() < range_match.start()]
        if candidate_values:
            return float(candidate_values[-1].group(1))

    return float(value_matches[0].group(1))


def extract_unit(line: str) -> str:
    match = UNIT_PATTERN.search(line)
    if not match:
        return ""
    return match.group(1).strip()


def unique_list(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
