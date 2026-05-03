from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_TEMPLATES_CACHE: dict[str, Any] | None = None


def load_templates() -> dict[str, Any]:
    global _TEMPLATES_CACHE
    if _TEMPLATES_CACHE is not None:
        return _TEMPLATES_CACHE

    templates: dict[str, Any] = {}
    if not TEMPLATE_DIR.exists():
        _TEMPLATES_CACHE = templates
        return templates

    for template_path in sorted(TEMPLATE_DIR.glob("*.json")):
        try:
            payload = json.loads(template_path.read_text(encoding="utf-8"))
            templates[template_path.stem.lower()] = payload
        except Exception:
            logger.exception("Failed to load template file: %s", template_path)

    _TEMPLATES_CACHE = templates
    return templates
