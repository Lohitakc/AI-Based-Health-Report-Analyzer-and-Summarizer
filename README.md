# Agentic AI-Based Pathology Report Summarizer

## Objective
This project processes pathology PDF reports and returns:
- structured parameter table (`parameter`, `value`, `unit`, `range`, `status`)
- patient-friendly summary
- doctor-focused abnormal summary
- mandatory disclaimer
- downloadable PDF report

The workflow uses a LangGraph multi-agent pipeline and RAG over trusted medical source notes (WHO, CDC, Mayo Clinic, NHS).

## Tech Stack
- Backend: FastAPI (Python)
- PDF Extraction: `pdfplumber`
- Agent Orchestration: LangChain + LangGraph
- Vector DB: ChromaDB (local)
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Free LLM: local Ollama model (optional, fallback logic included)
- Frontend: HTML + CSS + JavaScript

## Project Structure
```text
app/
  core/                 # parsing + analysis logic
  llm/                  # optional local free LLM wrapper
  pipeline/             # LangGraph state + agents + graph
  rag/                  # Chroma ingestion + retrieval + range resolver
  config.py
  main.py
frontend/
  index.html            # first page (upload)
  report.html           # second page (results)
  styles/
    base.css
    upload.css
    report.css
  scripts/
    upload-page.js
    report-page.js
data/medical_sources/   # trusted source RAG knowledge files
```

## Multi-Agent Pipeline (LangGraph)
1. PDF Extraction Agent: extract report text using `pdfplumber`
2. Parsing Agent: parse `{parameter, value, unit, range}`
3. Analysis Agent: compare value to range and classify `LOW/NORMAL/HIGH/CRITICAL`
4. Retrieval Agent: fetch explanation context from Chroma RAG
5. Explanation Agent: generate patient-friendly summary
6. Doctor Summary Agent: generate concise abnormal findings
7. Safety Agent: enforce disclaimer and non-diagnostic output

## Reference Range Policy
1. If report includes a reference range, that range is used.
2. If missing, the system retrieves standard ranges from RAG trusted source documents.
3. Output marks each row as:
   - `Based on report range`
   - `Based on standard medical reference`

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.rag.ingest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open: `http://127.0.0.1:8000`

## API
### `POST /upload`
Form-data input:
- `file`: pathology PDF

Response:
```json
{
  "table": [
    {
      "parameter": "Hemoglobin",
      "value": 11.2,
      "unit": "g/dL",
      "range": "13.0 - 17.0",
      "status": "LOW",
      "range_source": "Based on report range"
    }
  ],
  "patient_summary": "....",
  "doctor_summary": "....",
  "disclaimer": "This is not a medical diagnosis. Consult a doctor."
}
```

### `POST /download-pdf`
JSON input:
```json
{
  "report_name": "My_Report",
  "table": [...],
  "patient_summary": "...",
  "doctor_summary": "...",
  "disclaimer": "This is not a medical diagnosis. Consult a doctor."
}
```

Output:
- PDF file download containing:
  - analysis table
  - patient summary
  - doctor summary
  - disclaimer

## Notes
- Only free/open components are used.
- Local LLM via Ollama is optional; fallback summaries run without it.
- This system is an educational support tool, not a diagnosis engine.
