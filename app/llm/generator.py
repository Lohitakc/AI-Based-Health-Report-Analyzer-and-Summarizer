from __future__ import annotations

import os
from functools import lru_cache

from app.config import OLLAMA_MODEL


class FreeMedicalLLM:
    def __init__(self) -> None:
        self.llm = None
        try:
            from langchain_ollama import ChatOllama

            self.llm = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", OLLAMA_MODEL),
                temperature=0.2,
            )
        except Exception:
            self.llm = None

    def generate(self, system_prompt: str, user_prompt: str, fallback_text: str) -> str:
        if self.llm is None:
            return fallback_text

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            response = self.llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
            text = str(response.content).strip()
            return text if text else fallback_text
        except Exception:
            return fallback_text


@lru_cache(maxsize=1)
def get_free_llm() -> FreeMedicalLLM:
    return FreeMedicalLLM()

