from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Iterable
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas import DownloadPDFRequest


def _status_color(status: str):
    if status == "NORMAL":
        return colors.HexColor("#1F8A4D")
    if status in {"LOW", "HIGH"}:
        return colors.HexColor("#C65508")
    return colors.HexColor("#B42318")


def _safe_lines(text: str) -> Iterable[str]:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            yield cleaned


def _cell(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text), style)


def build_pdf_report(payload: DownloadPDFRequest) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#0F3B57"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#3A5366"),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0F3B57"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
    )
    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=body_style,
        leftIndent=12,
        bulletIndent=0,
        spaceAfter=4,
    )
    table_header_style = ParagraphStyle(
        "TableHeaderStyle",
        parent=styles["Normal"],
        fontSize=9.2,
        leading=11,
        textColor=colors.HexColor("#0F3B57"),
        fontName="Helvetica-Bold",
    )
    table_cell_style = ParagraphStyle(
        "TableCellStyle",
        parent=styles["Normal"],
        fontSize=8.8,
        leading=10.8,
        textColor=colors.HexColor("#0F172A"),
        wordWrap="CJK",
    )
    disclaimer_style = ParagraphStyle(
        "DisclaimerStyle",
        parent=body_style,
        textColor=colors.HexColor("#7A271A"),
        backColor=colors.HexColor("#FFF5E9"),
        borderColor=colors.HexColor("#F4C67A"),
        borderWidth=0.5,
        borderPadding=6,
        borderRadius=4,
        spaceBefore=8,
    )

    story = []
    story.append(Paragraph("Agentic AI Pathology Report Summary", title_style))
    story.append(
        Paragraph(
            f"Report Name: {escape(payload.report_name)}<br/>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            subtitle_style,
        )
    )

    story.append(Paragraph("Analysis Table", section_style))
    table_data = [
        [
            _cell("Parameter", table_header_style),
            _cell("Value", table_header_style),
            _cell("Range", table_header_style),
            _cell("Status", table_header_style),
            _cell("Range Source", table_header_style),
        ]
    ]

    for idx, row in enumerate(payload.table, start=1):
        value_label = f"{row.value} {row.unit}".strip()
        status_style = ParagraphStyle(
            f"TableStatusStyle{idx}",
            parent=table_cell_style,
            textColor=_status_color(row.status),
            fontName="Helvetica-Bold" if row.status in {"LOW", "HIGH", "CRITICAL"} else "Helvetica",
        )
        table_data.append(
            [
                _cell(str(row.parameter), table_cell_style),
                _cell(value_label, table_cell_style),
                _cell(str(row.range), table_cell_style),
                _cell(str(row.status), status_style),
                _cell(str(row.range_source), table_cell_style),
            ]
        )

    table = Table(table_data, colWidths=[1.45 * inch, 1.25 * inch, 1.35 * inch, 0.95 * inch, 1.95 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7F1FA")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D3DCE6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FBFF")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)

    story.append(Spacer(1, 8))
    story.append(Paragraph("Patient Summary", section_style))
    patient_lines = list(_safe_lines(payload.patient_summary))
    if patient_lines:
        for line in patient_lines:
            if line.startswith("- "):
                story.append(Paragraph(escape(line[2:]), bullet_style, bulletText="-"))
            elif line[:3] in {"1. ", "2. ", "3. ", "4. ", "5. "}:
                story.append(Paragraph(escape(line), bullet_style))
            else:
                story.append(Paragraph(escape(line), body_style))
    else:
        story.append(Paragraph("No patient summary generated.", body_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Doctor Summary", section_style))
    doctor_lines = list(_safe_lines(payload.doctor_summary))
    if doctor_lines:
        for line in doctor_lines:
            if line.startswith("- "):
                story.append(Paragraph(escape(line[2:]), bullet_style, bulletText="-"))
            else:
                story.append(Paragraph(escape(line), body_style))
    else:
        story.append(Paragraph("No doctor summary generated.", body_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph(escape(payload.disclaimer), disclaimer_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

