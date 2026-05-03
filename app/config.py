import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "medical_sources"
CHROMA_DIR = BASE_DIR / "db" / "chroma"
UPLOAD_DIR = BASE_DIR / "uploads"
FRONTEND_DIR = BASE_DIR / "frontend"

DISCLAIMER = "This is not a medical diagnosis. Consult a doctor."

OLLAMA_MODEL = "llama3.2"


def _env_flag(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


USE_MCP = _env_flag("USE_MCP", True)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "OLLAMA").strip().upper()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
