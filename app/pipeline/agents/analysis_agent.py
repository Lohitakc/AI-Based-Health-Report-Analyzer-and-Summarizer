from __future__ import annotations

from app.core.analysis import classify_value, format_range, parse_range_string
from app.pipeline.state import PipelineState
from app.rag.range_resolver import resolve_range_from_rag
from app.rag.vectorstore import get_vector_store


def analysis_agent(state: PipelineState) -> PipelineState:
    parsed_rows = state.get("parsed_rows", [])
    vector_store = get_vector_store()
    analyzed_rows: list[dict] = []

    for row in parsed_rows:
        parameter = row.get("parameter", "").strip()
        value = float(row.get("value", 0.0))
        unit = (row.get("unit") or "").strip()
        range_text = (row.get("reference_range") or "").strip()
        range_source = "Based on report range"
        source_name = "Report reference range"
        source_url = ""

        parsed_range = parse_range_string(range_text)
        if not parsed_range:
            resolved = resolve_range_from_rag(parameter, vector_store)
            if resolved:
                minimum = float(resolved["minimum"])
                maximum = float(resolved["maximum"])
                parsed_range = (minimum, maximum)
                range_text = format_range(minimum, maximum)
                if not unit:
                    unit = str(resolved.get("unit", "")).strip()
                range_source = "Based on standard medical reference"
                source_name = str(resolved.get("source_name", "")).strip() or "Standard medical reference"
                source_url = str(resolved.get("source_url", "")).strip()
            else:
                range_source = "Based on standard medical reference"
                source_name = "Standard medical reference"

        if parsed_range:
            status = classify_value(value, parsed_range[0], parsed_range[1])
        else:
            status = "NORMAL"
            if not range_text:
                range_text = "Not available"

        analyzed_rows.append(
            {
                "parameter": parameter,
                "value": value,
                "unit": unit,
                "range": range_text,
                "status": status,
                "range_source": range_source,
                "source_name": source_name,
                "source_url": source_url,
            }
        )

    return {"analyzed_rows": analyzed_rows}
