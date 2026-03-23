from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.config import DISCLAIMER, FRONTEND_DIR, UPLOAD_DIR
from app.pipeline.graph import run_pipeline
from app.rag.vectorstore import get_vector_store
from app.reporting.pdf_export import build_pdf_report
from app.schemas import DownloadPDFRequest, TableRow, UploadResponse

app = FastAPI(title="Agentic AI-Based Pathology Report Summarizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.on_event("startup")
def on_startup() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    get_vector_store().ingest(force_rebuild=False)


@app.get("/")
def root() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(index_path)


@app.get("/report")
def report_page() -> FileResponse:
    report_path = FRONTEND_DIR / "report.html"
    return FileResponse(report_path)


@app.post("/upload", response_model=UploadResponse)
async def upload_report(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temp_name = f"{uuid4()}.pdf"
    temp_path = UPLOAD_DIR / temp_name

    try:
        contents = await file.read()
        temp_path.write_bytes(contents)

        state = run_pipeline(str(temp_path))
        analyzed_rows = state.get("analyzed_rows", [])

        table = [
            TableRow(
                parameter=row.get("parameter", ""),
                value=float(row.get("value", 0.0)),
                unit=row.get("unit", ""),
                range=row.get("range", "Not available"),
                status=row.get("status", "NORMAL"),
                range_source=(
                    "Report reference range"
                    if row.get("range_source", "Based on report range") == "Based on report range"
                    else row.get("source_name", "Standard medical reference")
                ),
                source_basis=row.get("range_source", "Based on report range"),
                source_url=row.get("source_url", ""),
            )
            for row in analyzed_rows
        ]

        return UploadResponse(
            table=table,
            report_type=state.get("report_type", "Unknown"),
            patient_summary=state.get("patient_summary", "No summary generated."),
            doctor_summary=state.get("doctor_summary", "No doctor summary generated."),
            disclaimer=state.get("disclaimer", DISCLAIMER),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process report: {exc}") from exc
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


@app.post("/download-pdf")
async def download_pdf(payload: DownloadPDFRequest) -> Response:
    try:
        pdf_bytes = build_pdf_report(payload)
        safe_name = payload.report_name.strip().replace(" ", "_") or "Pathology_Report"
        filename = f"{safe_name}.pdf"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {exc}") from exc
