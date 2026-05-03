from __future__ import annotations

import logging

from app.mcp import get_mcp_server
from app.pipeline.state import PipelineState
from app.rag.range_resolver import extract_source_from_context
from app.rag.vectorstore import get_vector_store

logger = logging.getLogger(__name__)


def _compact_snippet(text: str, max_len: int = 260) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def retrieval_agent(state: PipelineState) -> PipelineState:
    analyzed_rows = state.get("analyzed_rows", [])
    vector_store = get_vector_store()
    mcp = get_mcp_server()

    retrieved_context: dict[str, list[dict[str, str]]] = {}
    for row in analyzed_rows:
        if row.get("status") == "NORMAL":
            continue

        parameter = row["parameter"]
        query = f"{parameter} high low interpretation and simple lifestyle advice"
        try:
            mcp_result = mcp.execute_tool(
                "retrieve_context_tool",
                {"parameter_name": parameter, "top_k": 3, "query": query},
            )
            chunks = [str(chunk) for chunk in mcp_result.get("top_k_chunks", [])]
        except Exception:
            logger.exception("retrieve_context_tool failed for '%s'. Falling back.", parameter)
            docs = vector_store.retrieve(query, k=3)
            chunks = [doc.page_content for doc in docs]

        contexts: list[dict[str, str]] = []

        for chunk in chunks:
            source, url = extract_source_from_context(chunk)
            contexts.append(
                {
                    "snippet": _compact_snippet(chunk),
                    "source": source,
                    "url": url,
                }
            )

        retrieved_context[parameter] = contexts

    return {"retrieved_context": retrieved_context}
