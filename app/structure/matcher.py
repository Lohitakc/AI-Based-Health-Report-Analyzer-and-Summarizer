from __future__ import annotations

import difflib
import re
from typing import Any

from app.structure.utils import extract_ranges, extract_unit, extract_value, normalize_text


def _token_overlap_similarity(left: str, right: str) -> float:
    left_tokens = {token for token in left.split() if token}
    right_tokens = {token for token in right.split() if token}
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    if union == 0:
        return 0.0
    return overlap / union


def _name_similarity(candidate_name: str, aliases: list[str]) -> float:
    if not aliases:
        return 0.0

    normalized_aliases = [normalize_text(alias) for alias in aliases if alias]
    if not normalized_aliases:
        return 0.0

    fuzzy_hit = difflib.get_close_matches(candidate_name, normalized_aliases, n=1, cutoff=0.0)
    best_alias = fuzzy_hit[0] if fuzzy_hit else normalized_aliases[0]
    fuzzy_score = difflib.SequenceMatcher(None, candidate_name, best_alias).ratio()
    token_score = _token_overlap_similarity(candidate_name, best_alias)
    return max(fuzzy_score, token_score)


def _extract_name_candidate(line: str) -> str:
    numeric_match = re.search(r"-?\d+(?:\.\d+)?", line)
    if numeric_match:
        return normalize_text(line[: numeric_match.start()].strip(" :|-"))
    return normalize_text(line)


def _normalize_ranges(ranges: list[Any]) -> list[list[float]]:
    normalized: list[list[float]] = []
    for item in ranges:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        normalized.append([float(item[0]), float(item[1])])
    return normalized


def match_parameter(line: str, templates: dict[str, Any], current_section: str) -> dict[str, Any] | None:
    normalized_line = normalize_text(line)
    if not normalized_line:
        return None

    value = extract_value(line)
    if value is None:
        return None

    unit_raw = extract_unit(line).strip()
    unit = normalize_text(unit_raw)
    candidate_name = _extract_name_candidate(line)
    line_ranges = [[minimum, maximum] for minimum, maximum in extract_ranges(line)]
    if not candidate_name:
        return None

    best_match: dict[str, Any] | None = None
    best_score = 0.0
    current_section_normalized = normalize_text(current_section or "")

    for template_data in templates.values():
        sections = template_data.get("sections", {}) if isinstance(template_data, dict) else {}
        if not isinstance(sections, dict):
            continue

        for section_name, parameters in sections.items():
            if not isinstance(parameters, list):
                continue

            section_name_normalized = normalize_text(section_name)
            for parameter in parameters:
                if not isinstance(parameter, dict):
                    continue

                template_name = normalize_text(str(parameter.get("name", "")))
                aliases = [template_name]
                aliases.extend(normalize_text(str(alias)) for alias in parameter.get("aliases", []))
                aliases = [alias for alias in aliases if alias]
                if not aliases:
                    continue

                name_score = _name_similarity(candidate_name, aliases)
                unit_score = 0.0
                available_units = [
                    normalize_text(str(candidate_unit)) for candidate_unit in parameter.get("units", [])
                ]
                available_units = [candidate_unit for candidate_unit in available_units if candidate_unit]

                if unit and available_units:
                    unit_score = 1.0 if unit in available_units else 0.0
                elif not available_units:
                    unit_score = 0.5

                section_score = 1.0 if current_section_normalized and (
                    current_section_normalized == section_name_normalized
                ) else 0.0

                confidence = (0.5 * name_score) + (0.3 * unit_score) + (0.2 * section_score)
                if confidence <= best_score:
                    continue

                ranges = line_ranges or _normalize_ranges(parameter.get("ranges", []))
                if not ranges:
                    ranges = [[minimum, maximum] for minimum, maximum in extract_ranges(normalized_line)]

                best_score = confidence
                best_match = {
                    "parameter": template_name or candidate_name,
                    "value": value,
                    "unit": unit_raw,
                    "ranges": ranges,
                    "confidence": round(confidence, 4),
                }

    if best_match is None:
        return None
    if best_match["confidence"] < 0.7:
        return None
    return best_match
