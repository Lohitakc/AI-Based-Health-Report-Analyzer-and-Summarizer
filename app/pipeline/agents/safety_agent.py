from __future__ import annotations

from app.config import DISCLAIMER
from app.pipeline.state import PipelineState


def safety_agent(state: PipelineState) -> PipelineState:
    patient_summary = state.get("patient_summary", "")
    doctor_summary = state.get("doctor_summary", "")

    # Keep summaries non-diagnostic even if an optional local LLM is used.
    diagnostic_terms = ("you have", "diagnosed", "diagnosis is")
    for term in diagnostic_terms:
        patient_summary = patient_summary.replace(term, "possible finding")
        doctor_summary = doctor_summary.replace(term, "possible finding")

    return {
        "patient_summary": patient_summary.strip(),
        "doctor_summary": doctor_summary.strip(),
        "disclaimer": DISCLAIMER,
    }

