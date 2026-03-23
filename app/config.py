from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "medical_sources"
CHROMA_DIR = BASE_DIR / "db" / "chroma"
UPLOAD_DIR = BASE_DIR / "uploads"
FRONTEND_DIR = BASE_DIR / "frontend"

DISCLAIMER = "This is not a medical diagnosis. Consult a doctor."

OLLAMA_MODEL = "llama3.2"

