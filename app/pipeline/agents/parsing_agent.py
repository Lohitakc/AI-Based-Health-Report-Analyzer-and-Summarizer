from __future__ import annotations

from app.core.parsing import parse_parameters_from_text
from app.core.report_catalog import detect_report_type
from app.pipeline.state import PipelineState


def parsing_agent(state: PipelineState) -> PipelineState:
    raw_text = state.get("raw_text", "")
    report_type = detect_report_type(raw_text)
    parsed_rows = parse_parameters_from_text(raw_text, report_type=report_type)
    return {"report_type": report_type, "parsed_rows": parsed_rows}

