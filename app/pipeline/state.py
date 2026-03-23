from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    pdf_path: str
    raw_text: str
    report_type: str
    parsed_rows: list[dict[str, Any]]
    analyzed_rows: list[dict[str, Any]]
    retrieved_context: dict[str, list[dict[str, str]]]
    patient_summary: str
    doctor_summary: str
    disclaimer: str

