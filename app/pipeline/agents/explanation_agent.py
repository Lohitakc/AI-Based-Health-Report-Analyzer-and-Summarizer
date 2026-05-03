from __future__ import annotations

import logging

from app.llm.generator import get_free_llm
from app.mcp import get_mcp_server
from app.pipeline.state import PipelineState

logger = logging.getLogger(__name__)


DEFAULT_EXPLANATIONS = {
    "Hemoglobin": "This can affect oxygen delivery and may relate to anemia when low.",
    "RBC": "This reflects red blood cells that carry oxygen through the body.",
    "WBC": "This can change during infection or immune response.",
    "Platelets": "Platelets help blood clot and prevent bleeding.",
    "Neutrophils": "These are often linked to bacterial infection patterns.",
    "Lymphocytes": "These are often linked to viral infection patterns and immune activity.",
    "Fasting Glucose": "This indicates sugar control after not eating for several hours.",
    "Postprandial Glucose": "This shows how blood sugar behaves after food.",
    "Random Glucose": "This is a quick screening value for blood sugar control.",
    "Urea / BUN": "This can rise with dehydration or kidney stress.",
    "Creatinine": "This is a strong marker used to assess kidney filtration.",
    "Bilirubin": "This can rise in jaundice or liver/bile flow problems.",
    "AST": "This enzyme can rise when liver cells are stressed.",
    "ALT": "This enzyme can rise during liver inflammation or injury.",
    "ALP": "This can change with bile duct or liver conditions.",
    "GGT": "This can increase with liver stress, including alcohol-related stress.",
    "Cholesterol": "Higher levels can increase long-term heart risk.",
    "LDL": "Higher LDL can increase plaque buildup risk in blood vessels.",
    "HDL": "Lower HDL can reduce protective cardiovascular effect.",
    "Triglycerides": "Higher triglycerides can increase metabolic and heart risk.",
    "T3": "This hormone helps regulate metabolism and energy use.",
    "T4": "This hormone level is used to assess thyroid activity.",
    "TSH": "This is a key regulator for thyroid function.",
    "Urine Protein": "Protein in urine can indicate kidney filtering issues.",
    "Urine Glucose": "Glucose in urine can be linked to blood sugar overflow.",
    "Pus Cells": "Higher pus cells can suggest urinary tract inflammation or infection.",
}


def _build_fallback_summary(state: PipelineState) -> str:
    rows = state.get("analyzed_rows", [])
    contexts = state.get("retrieved_context", {})
    abnormal_rows = [row for row in rows if row.get("status") != "NORMAL"]

    if not rows:
        return "No measurable lab values were extracted from the report."
    if not abnormal_rows:
        return "\n".join(
            [
                "Overall",
                "Your extracted lab values are mostly within the listed reference ranges.",
                "",
                "What This Means",
                "- No major abnormality was detected in the extracted parameters.",
                "",
                "Healthy Habits",
                "1. Stay hydrated and maintain regular meals.",
                "2. Sleep well and stay physically active.",
                "3. Continue routine follow-up as advised by your doctor.",
            ]
        )

    lines: list[str] = []
    trusted_sources: set[str] = set()

    lines.extend(
        [
            "Overall",
            f"{len(abnormal_rows)} parameter(s) are outside the reference range.",
            "",
            "Key Findings",
        ]
    )

    for row in abnormal_rows:
        parameter = row["parameter"]
        value = row["value"]
        unit = row["unit"]
        status = row["status"]
        range_text = row["range"]
        explanation = DEFAULT_EXPLANATIONS.get(
            parameter,
            "This value should be interpreted in clinical context with your doctor.",
        )

        source_text = ""
        parameter_context = contexts.get(parameter, [])
        if parameter_context:
            top_context = parameter_context[0]
            source = top_context.get("source", "Trusted medical source")
            trusted_sources.add(source)
            source_text = f" (Source: {source})"

        lines.append(
            f"- {parameter}: {value} {unit} [{status}] (Reference: {range_text}). "
            f"{explanation}{source_text}"
        )

    lines.extend(
        [
            "",
            "What You Can Do",
            "1. Keep hydration, balanced meals, and regular sleep.",
            "2. Reduce sugar-rich and ultra-processed food intake where relevant.",
            "3. Avoid smoking and alcohol excess.",
            "4. Repeat tests or seek review if symptoms persist.",
        ]
    )
    if trusted_sources:
        lines.extend(
            [
                "",
                f"Trusted References Used: {', '.join(sorted(trusted_sources))}",
            ]
        )

    return "\n".join(lines)


def explanation_agent(state: PipelineState) -> PipelineState:
    fallback_summary = _build_fallback_summary(state)
    llm = get_free_llm()
    mcp = get_mcp_server()

    abnormal_rows = [row for row in state.get("analyzed_rows", []) if row.get("status") != "NORMAL"]
    user_prompt = (
        "Write a patient-friendly summary in simple language using these abnormal findings: "
        f"{abnormal_rows}.\n"
        "Format with short sections and line breaks:\n"
        "Overall\n"
        "Key Findings (bullet lines starting with '- ')\n"
        "What You Can Do (numbered steps)\n"
        "Trusted References Used\n"
        "Do not include raw URLs. Keep it non-diagnostic."
    )
    system_prompt = (
        "You are a medical report explainer. Use supportive and simple language. "
        "Do not diagnose. Do not prescribe medicines."
    )

    try:
        summary_result = mcp.execute_tool(
            "generate_text_tool",
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "fallback_text": fallback_summary,
            },
        )
        summary = str(summary_result.get("summary", "")).strip() or llm.generate(
            system_prompt,
            user_prompt,
            fallback_summary,
        )
    except Exception:
        logger.exception("generate_text_tool failed for explanation_agent. Falling back.")
        summary = llm.generate(system_prompt, user_prompt, fallback_summary)

    return {"patient_summary": summary}
