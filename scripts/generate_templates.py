from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.structure.extractor import extract_structure_from_pdf
from app.structure.utils import normalize_text, unique_list

SOURCE_DIR = BASE_DIR / "data" / "report_templates"
TARGET_DIR = BASE_DIR / "app" / "structure" / "templates"

REPORT_TYPES = ("cbc", "glucose", "lipid", "thyroid", "urine")


def _dedupe_ranges(ranges: list[list[float]]) -> list[list[float]]:
    unique: list[list[float]] = []
    seen: set[tuple[float, float]] = set()
    for item in ranges:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        minimum = round(float(item[0]), 3)
        maximum = round(float(item[1]), 3)
        key = (minimum, maximum)
        if key in seen:
            continue
        seen.add(key)
        unique.append([minimum, maximum])
    unique.sort(key=lambda x: (x[0], x[1]))
    return unique


def _merge_parameter(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    aliases = [normalize_text(alias) for alias in existing.get("aliases", [])]
    aliases.extend(normalize_text(alias) for alias in incoming.get("aliases", []))
    aliases = [alias for alias in aliases if alias]

    units = [normalize_text(unit) for unit in existing.get("units", [])]
    units.extend(normalize_text(unit) for unit in incoming.get("units", []))
    units = [unit for unit in units if unit]

    ranges = list(existing.get("ranges", [])) + list(incoming.get("ranges", []))

    return {
        "name": normalize_text(incoming.get("name", existing.get("name", ""))),
        "aliases": unique_list(aliases),
        "units": unique_list(units),
        "ranges": _dedupe_ranges(ranges),
    }


def _merge_structure(into_payload: dict[str, Any], structure_payload: dict[str, Any]) -> None:
    into_sections = into_payload.setdefault("sections", {})
    for section_name, parameters in structure_payload.get("sections", {}).items():
        section_key = normalize_text(section_name).replace(" ", "_")
        merged_section = into_sections.setdefault(section_key, {})

        for parameter in parameters:
            parameter_name = normalize_text(parameter.get("name", ""))
            if not parameter_name:
                continue
            if parameter_name not in merged_section:
                merged_section[parameter_name] = {
                    "name": parameter_name,
                    "aliases": unique_list([normalize_text(alias) for alias in parameter.get("aliases", []) if alias]),
                    "units": unique_list([normalize_text(unit) for unit in parameter.get("units", []) if unit]),
                    "ranges": _dedupe_ranges(parameter.get("ranges", [])),
                }
                continue

            merged_section[parameter_name] = _merge_parameter(merged_section[parameter_name], parameter)


def _finalize_payload(payload: dict[str, Any], report_type: str) -> dict[str, Any]:
    finalized_sections: dict[str, list[dict[str, Any]]] = {}
    for section_name, parameter_map in payload.get("sections", {}).items():
        rows = list(parameter_map.values())
        rows.sort(key=lambda item: item.get("name", ""))
        finalized_sections[section_name] = rows
    return {"report_type": report_type, "sections": finalized_sections}


def generate_templates() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    for report_type in REPORT_TYPES:
        source_folder = SOURCE_DIR / report_type
        aggregate: dict[str, Any] = {"sections": {}}
        target_path = TARGET_DIR / f"{report_type}.json"
        pdf_paths = sorted(source_folder.rglob("*.pdf")) if source_folder.exists() else []

        if not pdf_paths:
            if target_path.exists():
                print(f"No PDFs found for '{report_type}', keeping existing template: {target_path}")
                continue

            target_path.write_text(
                json.dumps({"report_type": report_type, "sections": {}}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"Template initialized: {target_path}")
            continue

        for pdf_path in pdf_paths:
            extracted = extract_structure_from_pdf(str(pdf_path))
            _merge_structure(aggregate, extracted)

        finalized_payload = _finalize_payload(aggregate, report_type)
        target_path.write_text(
            json.dumps(finalized_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Template generated: {target_path}")


if __name__ == "__main__":
    generate_templates()
