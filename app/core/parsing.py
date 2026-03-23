import re
from typing import Any

from app.core.report_catalog import get_parameter_definitions

RANGE_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:-|to|–|—)\s*(-?\d+(?:\.\d+)?)")
VALUE_PATTERN = re.compile(r"(?<![A-Za-z])(-?\d+(?:\.\d+)?)(?![A-Za-z])")

STOPWORDS = {
    "name",
    "patient",
    "age",
    "gender",
    "male",
    "female",
    "date",
    "time",
    "sample",
    "collected",
    "reported",
    "id",
}


def clean_line(line: str) -> str:
    line = line.replace("\t", " ")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def parse_range(range_text: str | None) -> tuple[float, float] | None:
    if not range_text:
        return None
    match = RANGE_PATTERN.search(range_text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def _extract_value_unit_range(line: str, alias: str) -> dict[str, Any] | None:
    lowered = line.lower()
    alias_start = lowered.find(alias)
    if alias_start < 0:
        return None

    search_text = line[alias_start + len(alias) :]
    value_match = VALUE_PATTERN.search(search_text)
    if not value_match:
        return None

    value = float(value_match.group(1))
    absolute_value_start = alias_start + len(alias) + value_match.start()
    absolute_value_end = alias_start + len(alias) + value_match.end()

    range_match = RANGE_PATTERN.search(line)
    range_text = ""
    minimum = None
    maximum = None
    range_start = len(line)

    if range_match:
        minimum = float(range_match.group(1))
        maximum = float(range_match.group(2))
        range_text = f"{minimum} - {maximum}"
        range_start = range_match.start()

    unit = line[absolute_value_end:range_start].strip(" :|")
    unit = re.sub(r"\s+", " ", unit)

    return {
        "value": value,
        "unit": unit,
        "reference_range": range_text,
        "min": minimum,
        "max": maximum,
    }


def _looks_like_measurement_line(line: str) -> bool:
    lowered = line.lower()
    if len(line) < 5:
        return False
    if not any(char.isdigit() for char in line):
        return False
    if any(lowered.startswith(word + " ") for word in STOPWORDS):
        return False
    return True


def _generic_parse(line: str) -> dict[str, Any] | None:
    if not _looks_like_measurement_line(line):
        return None

    value_matches = list(VALUE_PATTERN.finditer(line))
    range_match = RANGE_PATTERN.search(line)
    if not value_matches:
        return None

    if range_match:
        candidate_values = [match for match in value_matches if match.start() < range_match.start()]
        value_match = candidate_values[-1] if candidate_values else value_matches[0]
    else:
        value_match = value_matches[0]

    parameter = clean_line(line[: value_match.start()].strip(" :|-"))
    if len(parameter) < 2:
        return None
    if parameter.lower() in STOPWORDS:
        return None

    value = float(value_match.group(1))
    range_text = ""
    minimum = None
    maximum = None

    if range_match:
        minimum = float(range_match.group(1))
        maximum = float(range_match.group(2))
        range_text = f"{minimum} - {maximum}"
        unit_text = line[value_match.end() : range_match.start()]
    else:
        unit_text = line[value_match.end() :]

    unit = clean_line(unit_text.strip(" :|-"))
    return {
        "parameter": parameter,
        "value": value,
        "unit": unit,
        "reference_range": range_text,
        "min": minimum,
        "max": maximum,
    }


def parse_parameters_from_text(text: str, report_type: str) -> list[dict[str, Any]]:
    lines = [clean_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    parsed: list[dict[str, Any]] = []
    seen_parameters: set[str] = set()
    definitions = get_parameter_definitions(report_type)

    for line in lines:
        if not _looks_like_measurement_line(line):
            continue

        matched = False
        lowered = line.lower()

        for definition in definitions:
            selected_alias = next((alias for alias in definition.aliases if alias in lowered), None)
            if not selected_alias:
                continue

            extracted = _extract_value_unit_range(line, selected_alias)
            if not extracted:
                continue

            if definition.parameter in seen_parameters:
                matched = True
                break

            parsed.append(
                {
                    "parameter": definition.parameter,
                    "value": extracted["value"],
                    "unit": extracted["unit"],
                    "reference_range": extracted["reference_range"],
                    "min": extracted["min"],
                    "max": extracted["max"],
                }
            )
            seen_parameters.add(definition.parameter)
            matched = True
            break

        if matched:
            continue

        generic = _generic_parse(line)
        if not generic:
            continue
        if generic["parameter"] in seen_parameters:
            continue

        parsed.append(generic)
        seen_parameters.add(generic["parameter"])

    return parsed

