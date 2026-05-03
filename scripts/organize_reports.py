from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import pdfplumber

BASE_DIR = Path(__file__).resolve().parent.parent
TARGET_ROOT = BASE_DIR / "data" / "report_templates"

# Set to "lipid" if you want liver-function reports merged into the lipid folder.
LIVER_TARGET = "liver"

CATEGORY_KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "cbc": [
        ("haemogram", 10),
        ("haematology", 9),
        ("hemoglobin", 7),
        ("haemoglobin", 7),
        ("rbc", 6),
    ],
    "glucose": [
        ("glucose", 10),
        ("fasting", 4),
        ("postprandial", 4),
        ("random", 2),
    ],
    "kidney": [
        ("creatinine", 10),
        ("urea", 9),
        ("bun", 9),
    ],
    "liver": [
        ("liver function", 10),
        ("bilirubin", 9),
        ("alt", 7),
        ("ast", 7),
    ],
    "lipid": [
        ("lipid profile", 10),
        ("cholesterol", 9),
        ("triglycerides", 8),
        ("hdl", 7),
        ("ldl", 7),
    ],
    "thyroid": [
        ("thyroid", 10),
        ("t3", 8),
        ("t4", 8),
        ("tsh", 8),
    ],
    "urine": [
        ("urine routine", 10),
        ("urine examination", 10),
        ("urinalysis", 8),
    ],
}

CATEGORY_TIEBREAK_PRIORITY = [
    "cbc",
    "glucose",
    "kidney",
    "liver",
    "lipid",
    "thyroid",
    "urine",
]

REQUIRED_DIRS = {"cbc", "glucose", "lipid", "thyroid", "urine", "kidney", "unknown", LIVER_TARGET}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keyword_pattern(keyword: str) -> re.Pattern[str]:
    escaped = re.escape(keyword)
    # For single-token keywords, enforce word boundaries for better precision.
    if " " not in keyword:
        return re.compile(rf"\b{escaped}\b", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


def read_first_page_text(pdf_path: Path) -> str:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return ""
            return pdf.pages[0].extract_text() or ""
    except Exception:
        return ""


def classify_report(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return "unknown"

    category_scores: dict[str, int] = {category: 0 for category in CATEGORY_KEYWORDS}
    strongest_match_weight: dict[str, int] = {category: 0 for category in CATEGORY_KEYWORDS}

    for category, keyword_rules in CATEGORY_KEYWORDS.items():
        for keyword, weight in keyword_rules:
            pattern = keyword_pattern(keyword)
            if pattern.search(normalized):
                category_scores[category] += weight
                if weight > strongest_match_weight[category]:
                    strongest_match_weight[category] = weight

    best_category = "unknown"
    best_strongest_weight = 0
    best_total_score = 0

    for category in CATEGORY_TIEBREAK_PRIORITY:
        strongest = strongest_match_weight.get(category, 0)
        total = category_scores.get(category, 0)
        if strongest == 0:
            continue

        if strongest > best_strongest_weight:
            best_category = category
            best_strongest_weight = strongest
            best_total_score = total
            continue

        if strongest == best_strongest_weight and total > best_total_score:
            best_category = category
            best_total_score = total

    if best_category == "liver":
        return LIVER_TARGET

    return best_category


def ensure_directories() -> None:
    for folder_name in REQUIRED_DIRS:
        (TARGET_ROOT / folder_name).mkdir(parents=True, exist_ok=True)


def unique_destination_path(target_dir: Path, original_name: str) -> Path:
    destination = target_dir / original_name
    if not destination.exists():
        return destination

    stem = Path(original_name).stem
    suffix = Path(original_name).suffix or ".pdf"
    index = 1
    while True:
        candidate = target_dir / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def iter_pdf_files(input_dir: Path) -> list[Path]:
    return sorted(path for path in input_dir.glob("*.pdf") if path.is_file())


def organize_reports(input_dir: Path) -> None:
    ensure_directories()
    pdf_files = iter_pdf_files(input_dir)

    if not pdf_files:
        print(f"No PDF files found in: {input_dir}")
        return

    for pdf_path in pdf_files:
        first_page_text = read_first_page_text(pdf_path)
        category = classify_report(first_page_text)
        destination_dir = TARGET_ROOT / category
        destination_path = unique_destination_path(destination_dir, pdf_path.name)

        shutil.move(str(pdf_path), str(destination_path))

        if category == "unknown":
            print(f"[UNKNOWN] {pdf_path.name} -> unknown")
        else:
            print(f"[MOVED] {pdf_path.name} -> {category}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Organize pathology PDF reports into data/report_templates/* folders."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory containing raw PDF files to organize (default: current working directory).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory not found or invalid: {input_dir}")
    organize_reports(input_dir)


if __name__ == "__main__":
    main()
