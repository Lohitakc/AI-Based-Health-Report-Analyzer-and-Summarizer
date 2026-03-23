from __future__ import annotations

from app.llm.generator import get_free_llm
from app.pipeline.state import PipelineState


def _fallback_doctor_summary(state: PipelineState) -> str:
    report_type = state.get("report_type", "Unknown")
    rows = state.get("analyzed_rows", [])
    abnormal = [row for row in rows if row.get("status") != "NORMAL"]

    if not abnormal:
        return "\n".join(
            [
                f"Report Type: {report_type}",
                "Abnormal Findings",
                "- No major abnormal extracted parameters.",
                "Clinical Note",
                "- Correlate with clinical history and repeat if indicated.",
            ]
        )

    findings = [f"Report Type: {report_type}", "Abnormal Findings"]
    for row in abnormal:
        findings.append(
            f"- {row['parameter']}: {row['value']} {row['unit']} "
            f"(Ref: {row['range']}) -> {row['status']}"
        )
    findings.extend(
        [
            "Clinical Note",
            "- Prioritize follow-up for CRITICAL values, then HIGH/LOW values.",
            "- Integrate with symptoms, medications, and prior baseline reports.",
        ]
    )
    return "\n".join(findings)


def doctor_summary_agent(state: PipelineState) -> PipelineState:
    fallback = _fallback_doctor_summary(state)
    llm = get_free_llm()
    prompt = (
        "Create a concise clinical-style summary of only abnormal findings with line breaks.\n"
        "Use this format:\n"
        "Report Type\n"
        "Abnormal Findings (bullets)\n"
        "Clinical Note (bullets)\n"
        "No diagnosis.\n"
        f"Findings: {[row for row in state.get('analyzed_rows', []) if row.get('status') != 'NORMAL']}"
    )
    summary = llm.generate(
        "You summarize lab abnormalities for clinicians in concise style. No diagnosis.",
        prompt,
        fallback,
    )
    return {"doctor_summary": summary}
