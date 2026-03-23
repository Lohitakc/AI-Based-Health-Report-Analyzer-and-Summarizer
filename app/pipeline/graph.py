from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.pipeline.agents.analysis_agent import analysis_agent
from app.pipeline.agents.doctor_summary_agent import doctor_summary_agent
from app.pipeline.agents.explanation_agent import explanation_agent
from app.pipeline.agents.extraction_agent import pdf_extraction_agent
from app.pipeline.agents.parsing_agent import parsing_agent
from app.pipeline.agents.retrieval_agent import retrieval_agent
from app.pipeline.agents.safety_agent import safety_agent
from app.pipeline.state import PipelineState


@lru_cache(maxsize=1)
def get_pipeline():
    graph = StateGraph(PipelineState)
    graph.add_node("extract", pdf_extraction_agent)
    graph.add_node("parse", parsing_agent)
    graph.add_node("analyze", analysis_agent)
    graph.add_node("retrieve", retrieval_agent)
    graph.add_node("explain", explanation_agent)
    graph.add_node("doctor", doctor_summary_agent)
    graph.add_node("safety", safety_agent)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "parse")
    graph.add_edge("parse", "analyze")
    graph.add_edge("analyze", "retrieve")
    graph.add_edge("retrieve", "explain")
    graph.add_edge("explain", "doctor")
    graph.add_edge("doctor", "safety")
    graph.add_edge("safety", END)
    return graph.compile()


def run_pipeline(pdf_path: str) -> PipelineState:
    pipeline = get_pipeline()
    result = pipeline.invoke({"pdf_path": pdf_path})
    return result

