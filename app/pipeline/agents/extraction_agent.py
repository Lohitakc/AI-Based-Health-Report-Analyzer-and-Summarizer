from __future__ import annotations

import pdfplumber

from app.pipeline.state import PipelineState


def pdf_extraction_agent(state: PipelineState) -> PipelineState:
    pdf_path = state["pdf_path"]
    pages: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")

    return {"raw_text": "\n".join(pages)}

