from __future__ import annotations

import re
from typing import Any

from app.rag.vectorstore import MedicalVectorStore

RANGE_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:-|to|–|—)\s*(-?\d+(?:\.\d+)?)")
UNIT_PATTERN = re.compile(
    r"range:\s*-?\d+(?:\.\d+)?\s*(?:-|to|–|—)\s*-?\d+(?:\.\d+)?\s*([^\s|]+)",
    re.IGNORECASE,
)
SOURCE_PATTERN = re.compile(r"source:\s*([^|\n]+)", re.IGNORECASE)
URL_PATTERN = re.compile(r"url:\s*(https?://\S+)", re.IGNORECASE)


FALLBACK_RANGES: dict[str, dict[str, Any]] = {
    "Hemoglobin": {
        "minimum": 13.0,
        "maximum": 17.0,
        "unit": "g/dL",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919",
    },
    "RBC": {
        "minimum": 4.5,
        "maximum": 5.9,
        "unit": "million/uL",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919",
    },
    "WBC": {
        "minimum": 4.0,
        "maximum": 11.0,
        "unit": "x10^3/uL",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919",
    },
    "Platelets": {
        "minimum": 150.0,
        "maximum": 450.0,
        "unit": "x10^3/uL",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919",
    },
    "MCV": {
        "minimum": 80.0,
        "maximum": 100.0,
        "unit": "fL",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919",
    },
    "MCH": {
        "minimum": 27.0,
        "maximum": 33.0,
        "unit": "pg",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/complete-blood-count/about/pac-20384919",
    },
    "Neutrophils": {
        "minimum": 40.0,
        "maximum": 70.0,
        "unit": "%",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/blood-tests/",
    },
    "Lymphocytes": {
        "minimum": 20.0,
        "maximum": 40.0,
        "unit": "%",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/blood-tests/",
    },
    "Fasting Glucose": {
        "minimum": 70.0,
        "maximum": 100.0,
        "unit": "mg/dL",
        "source_name": "CDC",
        "source_url": "https://www.cdc.gov/diabetes/diabetes-testing/index.html",
    },
    "Postprandial Glucose": {
        "minimum": 120.0,
        "maximum": 160.0,
        "unit": "mg/dL",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/type-2-diabetes/",
    },
    "Random Glucose": {
        "minimum": 70.0,
        "maximum": 140.0,
        "unit": "mg/dL",
        "source_name": "CDC",
        "source_url": "https://www.cdc.gov/diabetes/diabetes-testing/index.html",
    },
    "Urea / BUN": {
        "minimum": 7.0,
        "maximum": 20.0,
        "unit": "mg/dL",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/blood-urea-nitrogen/about/pac-20384921",
    },
    "Creatinine": {
        "minimum": 0.74,
        "maximum": 1.35,
        "unit": "mg/dL",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/kidney-disease/diagnosis/",
    },
    "Bilirubin": {
        "minimum": 0.1,
        "maximum": 1.2,
        "unit": "mg/dL",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
    },
    "AST": {
        "minimum": 10.0,
        "maximum": 40.0,
        "unit": "U/L",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
    },
    "ALT": {
        "minimum": 7.0,
        "maximum": 56.0,
        "unit": "U/L",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
    },
    "ALP": {
        "minimum": 44.0,
        "maximum": 147.0,
        "unit": "U/L",
        "source_name": "Mayo Clinic",
        "source_url": "https://www.mayoclinic.org/tests-procedures/liver-function-tests/about/pac-20394595",
    },
    "GGT": {
        "minimum": 9.0,
        "maximum": 48.0,
        "unit": "U/L",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/liver-disease/",
    },
    "Cholesterol": {
        "minimum": 125.0,
        "maximum": 200.0,
        "unit": "mg/dL",
        "source_name": "CDC",
        "source_url": "https://www.cdc.gov/cholesterol/prevention/index.html",
    },
    "LDL": {
        "minimum": 0.0,
        "maximum": 100.0,
        "unit": "mg/dL",
        "source_name": "CDC",
        "source_url": "https://www.cdc.gov/cholesterol/prevention/index.html",
    },
    "HDL": {
        "minimum": 40.0,
        "maximum": 90.0,
        "unit": "mg/dL",
        "source_name": "CDC",
        "source_url": "https://www.cdc.gov/cholesterol/prevention/index.html",
    },
    "Triglycerides": {
        "minimum": 0.0,
        "maximum": 150.0,
        "unit": "mg/dL",
        "source_name": "CDC",
        "source_url": "https://www.cdc.gov/cholesterol/prevention/index.html",
    },
    "T3": {
        "minimum": 80.0,
        "maximum": 200.0,
        "unit": "ng/dL",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/underactive-thyroid-hypothyroidism/diagnosis/",
    },
    "T4": {
        "minimum": 5.0,
        "maximum": 12.0,
        "unit": "ug/dL",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/underactive-thyroid-hypothyroidism/diagnosis/",
    },
    "TSH": {
        "minimum": 0.4,
        "maximum": 4.0,
        "unit": "mIU/L",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/underactive-thyroid-hypothyroidism/diagnosis/",
    },
    "Urine Protein": {
        "minimum": 0.0,
        "maximum": 0.0,
        "unit": "negative",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/urine-test/",
    },
    "Urine Glucose": {
        "minimum": 0.0,
        "maximum": 0.0,
        "unit": "negative",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/urine-test/",
    },
    "Pus Cells": {
        "minimum": 0.0,
        "maximum": 5.0,
        "unit": "/hpf",
        "source_name": "NHS",
        "source_url": "https://www.nhs.uk/conditions/urinary-tract-infections-utis/",
    },
}


def _extract_from_document(content: str) -> dict[str, Any] | None:
    range_match = RANGE_PATTERN.search(content)
    if not range_match:
        return None
    source_match = SOURCE_PATTERN.search(content)
    url_match = URL_PATTERN.search(content)
    unit_match = UNIT_PATTERN.search(content)

    return {
        "minimum": float(range_match.group(1)),
        "maximum": float(range_match.group(2)),
        "unit": unit_match.group(1).strip() if unit_match else "",
        "source_name": source_match.group(1).strip() if source_match else "Standard medical reference",
        "source_url": url_match.group(1).strip() if url_match else "",
    }


def resolve_range_from_rag(parameter: str, vector_store: MedicalVectorStore) -> dict[str, Any] | None:
    query = f"{parameter} standard adult reference range"
    docs = vector_store.retrieve(query, k=4)
    lowered_parameter = parameter.lower()

    for doc in docs:
        content = doc.page_content
        if lowered_parameter not in content.lower():
            continue
        parsed = _extract_from_document(content)
        if parsed:
            return parsed

    if parameter in FALLBACK_RANGES:
        return FALLBACK_RANGES[parameter]

    return None


def extract_source_from_context(content: str) -> tuple[str, str]:
    source_match = SOURCE_PATTERN.search(content)
    url_match = URL_PATTERN.search(content)
    source = source_match.group(1).strip() if source_match else "Trusted medical source"
    url = url_match.group(1).strip() if url_match else ""
    return source, url

