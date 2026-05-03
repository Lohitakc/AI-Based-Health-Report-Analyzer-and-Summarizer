import logging
import re
from typing import Any

from app.core.report_catalog import get_parameter_definitions
from app.structure.matcher import match_parameter
from app.structure.templates import load_templates
from app.structure.utils import normalize_text

RANGE_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:-|to|\u2013|\u2014)\s*(-?\d+(?:\.\d+)?)")
VALUE_PATTERN = re.compile(r"(?<![A-Za-z])(-?\d+(?:\.\d+)?)(?![A-Za-z])")

logger = logging.getLogger(__name__)

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

SECTION_HEADERS = {
    "haematology": ("haematology", "hematology"),
    "biochemistry": ("biochemistry",),
    "clinical_pathology": ("clinical pathology",),
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


def _detect_section(line: str) -> str | None:
    normalized = normalize_text(line)
    for section_name, keywords in SECTION_HEADERS.items():
        if any(keyword in normalized for keyword in keywords):
            return section_name
    return None


def _canonicalize_template_parameter(parameter_name: str, definitions: list[Any]) -> str:
    normalized_target = normalize_text(parameter_name)
    if not normalized_target:
        return ""

    for definition in definitions:
        canonical_name = normalize_text(definition.parameter)
        aliases = {normalize_text(alias) for alias in definition.aliases}
        aliases.add(canonical_name)
        if normalized_target in aliases:
            return definition.parameter

    return parameter_name.strip()


def parse_parameters_from_text(text: str, report_type: str) -> list[dict[str, Any]]:
    lines = [clean_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    parsed: list[dict[str, Any]] = []
    seen_parameters: set[str] = set()
    definitions = get_parameter_definitions(report_type)
    templates = load_templates()
    current_section = ""

    for line in lines:
        detected_section = _detect_section(line)
        if detected_section:
            current_section = detected_section

        if not _looks_like_measurement_line(line):
            continue

        matched = False
        lowered = line.lower()
        template_result: dict[str, Any] | None = None

        try:
            template_result = match_parameter(line, templates, current_section)
        except Exception:
            logger.exception("FALLBACK_USED matcher exception for line='%s'", line)
            template_result = None

        if template_result is not None:
            parameter = _canonicalize_template_parameter(
                str(template_result.get("parameter", "")),
                definitions,
            )
            if parameter and parameter not in seen_parameters:
                ranges = template_result.get("ranges") or []
                range_text = ""
                minimum = None
                maximum = None
                if isinstance(ranges, list) and ranges:
                    first_range = ranges[0]
                    if isinstance(first_range, (list, tuple)) and len(first_range) == 2:
                        minimum = float(first_range[0])
                        maximum = float(first_range[1])
                        range_text = f"{minimum} - {maximum}"

                parsed.append(
                    {
                        "parameter": parameter,
                        "value": float(template_result.get("value", 0.0)),
                        "unit": str(template_result.get("unit", "")).strip(),
                        "reference_range": range_text,
                        "min": minimum,
                        "max": maximum,
                    }
                )
                seen_parameters.add(parameter)
                logger.info(
                    "MATCHED_TEMPLATE parameter='%s' confidence=%s line='%s'",
                    parameter,
                    template_result.get("confidence"),
                    line,
                )
                matched = True
            else:
                logger.info("FALLBACK_USED template duplicate/invalid line='%s'", line)
        else:
            logger.info("FALLBACK_USED line='%s'", line)

        if matched:
            continue

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
            logger.info("UNMATCHED_LINE line='%s'", line)
            continue
        if generic["parameter"] in seen_parameters:
            continue

        parsed.append(generic)
        seen_parameters.add(generic["parameter"])

    return parsed
