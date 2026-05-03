from __future__ import annotations

from app.core.analysis import classify_value
from app.llm.generator import get_free_llm
from app.mcp.schemas import (
    ClassifyValueInput,
    ClassifyValueOutput,
    GenerateTextInput,
    GenerateTextOutput,
    MCPTool,
    ResolveRangeInput,
    ResolveRangeOutput,
    RetrieveContextInput,
    RetrieveContextOutput,
)
from app.rag.range_resolver import resolve_range_from_rag
from app.rag.vectorstore import get_vector_store


def _retrieve_context(payload: RetrieveContextInput) -> RetrieveContextOutput:
    vector_store = get_vector_store()
    query = payload.query or f"{payload.parameter_name} high low interpretation and simple lifestyle advice"
    docs = vector_store.retrieve(query, k=payload.top_k)
    return RetrieveContextOutput(top_k_chunks=[doc.page_content for doc in docs])


def _resolve_range(payload: ResolveRangeInput) -> ResolveRangeOutput:
    vector_store = get_vector_store()
    resolved = resolve_range_from_rag(payload.parameter_name, vector_store)
    if not resolved:
        return ResolveRangeOutput(range=None)

    return ResolveRangeOutput(
        range={
            "minimum": float(resolved["minimum"]),
            "maximum": float(resolved["maximum"]),
            "unit": str(resolved.get("unit", "")).strip(),
            "source_name": str(resolved.get("source_name", "")).strip() or "Standard medical reference",
            "source_url": str(resolved.get("source_url", "")).strip(),
        }
    )


def _classify_value(payload: ClassifyValueInput) -> ClassifyValueOutput:
    status = classify_value(payload.value, payload.minimum, payload.maximum)
    return ClassifyValueOutput(status=status)


def _generate_text(payload: GenerateTextInput) -> GenerateTextOutput:
    llm = get_free_llm()
    summary = llm.generate(
        payload.system_prompt,
        payload.user_prompt,
        payload.fallback_text,
    )
    return GenerateTextOutput(summary=summary)


def build_default_tools() -> list[MCPTool]:
    return [
        MCPTool(
            name="retrieve_context_tool",
            description="Retrieve top-k medical context chunks for a lab parameter.",
            input_schema=RetrieveContextInput,
            output_schema=RetrieveContextOutput,
            handler=_retrieve_context,
            fallback_handler=_retrieve_context,
        ),
        MCPTool(
            name="resolve_range_tool",
            description="Resolve standard reference range details for a lab parameter.",
            input_schema=ResolveRangeInput,
            output_schema=ResolveRangeOutput,
            handler=_resolve_range,
            fallback_handler=_resolve_range,
        ),
        MCPTool(
            name="classify_value_tool",
            description="Classify a value against numeric reference bounds.",
            input_schema=ClassifyValueInput,
            output_schema=ClassifyValueOutput,
            handler=_classify_value,
            fallback_handler=_classify_value,
        ),
        MCPTool(
            name="generate_text_tool",
            description="Generate patient/doctor text summary with guarded fallback.",
            input_schema=GenerateTextInput,
            output_schema=GenerateTextOutput,
            handler=_generate_text,
            fallback_handler=_generate_text,
        ),
    ]
