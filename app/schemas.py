from typing import Literal

from pydantic import BaseModel, Field


class TableRow(BaseModel):
    parameter: str = Field(..., description="Lab parameter name")
    value: float = Field(..., description="Measured numeric value")
    unit: str = Field(default="", description="Measurement unit")
    range: str = Field(..., description="Reference range string")
    status: Literal["LOW", "NORMAL", "HIGH", "CRITICAL"] = Field(
        ..., description="Status after range comparison"
    )
    range_source: str = Field(..., description="Display source used for interpretation")
    source_basis: str = Field(
        default="Based on report range",
        description="Whether this came from report range or standard reference",
    )
    source_url: str = Field(default="", description="Reference URL when available")


class UploadResponse(BaseModel):
    table: list[TableRow]
    report_type: str = "Unknown"
    patient_summary: str
    doctor_summary: str
    disclaimer: str


class DownloadPDFRequest(BaseModel):
    report_name: str = "Pathology_Report"
    table: list[TableRow]
    patient_summary: str
    doctor_summary: str
    disclaimer: str
