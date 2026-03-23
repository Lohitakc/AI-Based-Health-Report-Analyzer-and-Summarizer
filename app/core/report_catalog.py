from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterDefinition:
    parameter: str
    report_type: str
    aliases: tuple[str, ...]


PARAMETER_DEFINITIONS = [
    ParameterDefinition(
        parameter="Hemoglobin",
        report_type="CBC",
        aliases=("hemoglobin", "haemoglobin", "hb"),
    ),
    ParameterDefinition(
        parameter="RBC",
        report_type="CBC",
        aliases=("rbc", "red blood cell"),
    ),
    ParameterDefinition(
        parameter="WBC",
        report_type="CBC",
        aliases=("wbc", "white blood cell", "total leucocyte count", "total leukocyte count"),
    ),
    ParameterDefinition(
        parameter="Platelets",
        report_type="CBC",
        aliases=("platelet", "platelets", "platelet count"),
    ),
    ParameterDefinition(parameter="MCV", report_type="CBC", aliases=("mcv",)),
    ParameterDefinition(parameter="MCH", report_type="CBC", aliases=("mch",)),
    ParameterDefinition(
        parameter="Neutrophils",
        report_type="CBC",
        aliases=("neutrophils", "neutrophil"),
    ),
    ParameterDefinition(
        parameter="Lymphocytes",
        report_type="CBC",
        aliases=("lymphocytes", "lymphocyte"),
    ),
    ParameterDefinition(
        parameter="Fasting Glucose",
        report_type="Glucose",
        aliases=(
            "fasting glucose",
            "fasting blood sugar",
            "fasting plasma glucose",
            "fbs",
        ),
    ),
    ParameterDefinition(
        parameter="Postprandial Glucose",
        report_type="Glucose",
        aliases=("postprandial glucose", "post prandial glucose", "ppbs", "2 hour glucose", "2 hr glucose"),
    ),
    ParameterDefinition(
        parameter="Random Glucose",
        report_type="Glucose",
        aliases=("random glucose", "random blood sugar", "rbs"),
    ),
    ParameterDefinition(
        parameter="Urea / BUN",
        report_type="Kidney",
        aliases=("urea", "bun", "blood urea nitrogen"),
    ),
    ParameterDefinition(
        parameter="Creatinine",
        report_type="Kidney",
        aliases=("creatinine", "serum creatinine"),
    ),
    ParameterDefinition(
        parameter="Bilirubin",
        report_type="LFT",
        aliases=("bilirubin", "total bilirubin"),
    ),
    ParameterDefinition(parameter="AST", report_type="LFT", aliases=("ast", "sgot")),
    ParameterDefinition(parameter="ALT", report_type="LFT", aliases=("alt", "sgpt")),
    ParameterDefinition(
        parameter="ALP",
        report_type="LFT",
        aliases=("alp", "alkaline phosphatase"),
    ),
    ParameterDefinition(
        parameter="GGT",
        report_type="LFT",
        aliases=("ggt", "gamma glutamyl transferase"),
    ),
    ParameterDefinition(
        parameter="Cholesterol",
        report_type="Lipid",
        aliases=("cholesterol", "total cholesterol"),
    ),
    ParameterDefinition(parameter="LDL", report_type="Lipid", aliases=("ldl", "ldl cholesterol")),
    ParameterDefinition(parameter="HDL", report_type="Lipid", aliases=("hdl", "hdl cholesterol")),
    ParameterDefinition(
        parameter="Triglycerides",
        report_type="Lipid",
        aliases=("triglycerides", "triglyceride"),
    ),
    ParameterDefinition(parameter="T3", report_type="Thyroid", aliases=("t3", "triiodothyronine")),
    ParameterDefinition(parameter="T4", report_type="Thyroid", aliases=("t4", "thyroxine")),
    ParameterDefinition(
        parameter="TSH",
        report_type="Thyroid",
        aliases=("tsh", "thyroid stimulating hormone"),
    ),
    ParameterDefinition(
        parameter="Urine Protein",
        report_type="Urine",
        aliases=("urine protein", "protein"),
    ),
    ParameterDefinition(
        parameter="Urine Glucose",
        report_type="Urine",
        aliases=("urine glucose", "urine sugar"),
    ),
    ParameterDefinition(
        parameter="Pus Cells",
        report_type="Urine",
        aliases=("pus cells", "pus cell"),
    ),
]


REPORT_KEYWORDS = {
    "CBC": ("cbc", "complete blood count", "haemogram", "hemogram"),
    "Glucose": ("glucose", "fasting", "postprandial", "ppbs", "blood sugar", "diabetes"),
    "LFT": ("liver function", "lft", "bilirubin", "alt", "ast", "ggt", "alkaline phosphatase"),
    "Lipid": ("lipid", "cholesterol", "triglycerides", "hdl", "ldl"),
    "Thyroid": ("thyroid", "t3", "t4", "tsh"),
    "Urine": ("urine routine", "urinalysis", "pus cells", "urine protein", "urine sugar"),
    "Kidney": ("urea", "bun", "creatinine", "renal"),
}


def detect_report_type(text: str) -> str:
    lowered = text.lower()
    best_type = "Unknown"
    best_score = 0
    for report_type, keywords in REPORT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_type = report_type
            best_score = score
    return best_type


def get_parameter_definitions(report_type: str) -> list[ParameterDefinition]:
    if report_type == "Unknown":
        return list(PARAMETER_DEFINITIONS)
    prioritized = [item for item in PARAMETER_DEFINITIONS if item.report_type == report_type]
    remaining = [item for item in PARAMETER_DEFINITIONS if item.report_type != report_type]
    return prioritized + remaining

