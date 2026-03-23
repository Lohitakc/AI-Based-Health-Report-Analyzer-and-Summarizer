from __future__ import annotations

from app.pipeline.state import PipelineState
from app.rag.range_resolver import extract_source_from_context
from app.rag.vectorstore import get_vector_store


def _compact_snippet(text: str, max_len: int = 260) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def retrieval_agent(state: PipelineState) -> PipelineState:
    analyzed_rows = state.get("analyzed_rows", [])
    vector_store = get_vector_store()

    retrieved_context: dict[str, list[dict[str, str]]] = {}
    for row in analyzed_rows:
        if row.get("status") == "NORMAL":
            continue

        parameter = row["parameter"]
        query = f"{parameter} high low interpretation and simple lifestyle advice"
        docs = vector_store.retrieve(query, k=3)
        contexts: list[dict[str, str]] = []

        for doc in docs:
            source, url = extract_source_from_context(doc.page_content)
            contexts.append(
                {
                    "snippet": _compact_snippet(doc.page_content),
                    "source": source,
                    "url": url,
                }
            )

        retrieved_context[parameter] = contexts

    return {"retrieved_context": retrieved_context}

