from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pdfplumber

from app.structure.utils import extract_ranges, extract_unit, normalize_text, unique_list

SECTION_HEADER_RULES = {
    "haematology": ("haematology", "hematology"),
    "biochemistry": ("biochemistry",),
    "clinical_pathology": ("clinical pathology",),
}

SHORT_FORM_MAP = {
    "hemoglobin": "hb",
    "haemoglobin": "hb",
    "red blood cell": "rbc",
    "white blood cell": "wbc",
    "platelet count": "plt",
}


def _detect_section(line: str) -> str | None:
    normalized = normalize_text(line)
    for section, keywords in SECTION_HEADER_RULES.items():
        if any(keyword in normalized for keyword in keywords):
            return section
    return None


def _extract_parameter_name(line: str) -> str:
    first_number = re.search(r"-?\d+(?:\.\d+)?", line)
    if first_number:
        name = line[: first_number.start()]
    else:
        unit = extract_unit(line)
        name = line.split(unit, 1)[0] if unit else line
    return normalize_text(name.strip(" :|-"))


def _generate_aliases(parameter_name: str) -> list[str]:
    aliases: list[str] = []
    cleaned = normalize_text(parameter_name.replace(",", " "))
    if cleaned:
        aliases.append(cleaned)

    comma_removed = normalize_text(parameter_name.replace(",", ""))
    if comma_removed and comma_removed not in aliases:
        aliases.append(comma_removed)

    short_form = SHORT_FORM_MAP.get(cleaned)
    if short_form:
        aliases.append(short_form)

    tokens = [token for token in cleaned.split() if token]
    if len(tokens) > 1:
        acronym = "".join(token[0] for token in tokens)
        if 2 <= len(acronym) <= 5:
            aliases.append(acronym)

    return unique_list([alias for alias in aliases if alias])


def _is_valid_parameter_line(line: str) -> bool:
    normalized = normalize_text(line)
    if len(normalized) < 4:
        return False
    if not extract_unit(normalized):
        return False
    if not extract_ranges(normalized):
        return False
    return True


def extract_structure_from_pdf(file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    section_map: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    current_section = "unknown"

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            for raw_line in page_text.splitlines():
                line = normalize_text(raw_line)
                if not line:
                    continue

                section = _detect_section(line)
                if section:
                    current_section = section
                    continue

                if not _is_valid_parameter_line(line):
                    continue

                parameter_name = _extract_parameter_name(line)
                if not parameter_name or len(parameter_name) < 2:
                    continue

                aliases = _generate_aliases(parameter_name)
                unit = extract_unit(line)
                ranges = [[minimum, maximum] for minimum, maximum in extract_ranges(line)]

                existing = section_map[current_section].get(parameter_name)
                if not existing:
                    section_map[current_section][parameter_name] = {
                        "name": parameter_name,
                        "aliases": aliases,
                        "units": [unit] if unit else [],
                        "ranges": ranges,
                    }
                    continue

                existing["aliases"] = unique_list(existing["aliases"] + aliases)
                if unit and unit not in existing["units"]:
                    existing["units"].append(unit)

                known_ranges = {(float(item[0]), float(item[1])) for item in existing["ranges"]}
                for minimum, maximum in ranges:
                    range_tuple = (float(minimum), float(maximum))
                    if range_tuple not in known_ranges:
                        existing["ranges"].append([range_tuple[0], range_tuple[1]])
                        known_ranges.add(range_tuple)

    sections: dict[str, list[dict[str, Any]]] = {}
    for section_name, parameters in section_map.items():
        if not parameters:
            continue
        sections[section_name] = list(parameters.values())

    return {"sections": sections}
