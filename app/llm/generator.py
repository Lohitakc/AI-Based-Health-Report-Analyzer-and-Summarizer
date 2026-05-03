from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from urllib import error, request

from app.config import GROQ_MODEL, LLM_PROVIDER, OLLAMA_MODEL

logger = logging.getLogger(__name__)


class FreeMedicalLLM:
    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).strip().upper()
        self.ollama_llm = None
        self.groq_llm = None
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model = os.getenv("GROQ_MODEL", GROQ_MODEL).strip() or GROQ_MODEL

        if self.provider == "OLLAMA":
            self._init_ollama()
        elif self.provider == "GROQ":
            self._init_groq()
        else:
            logger.warning("Unsupported LLM_PROVIDER '%s'. Falling back to template text.", self.provider)

    def _init_ollama(self) -> None:
        try:
            from langchain_ollama import ChatOllama

            self.ollama_llm = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", OLLAMA_MODEL),
                temperature=0.2,
            )
        except Exception:
            self.ollama_llm = None

    def _init_groq(self) -> None:
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not set. Falling back to template text.")
            return

        try:
            from langchain_groq import ChatGroq

            self.groq_llm = ChatGroq(
                model=self.groq_model,
                temperature=0.2,
                api_key=self.groq_api_key,
            )
        except Exception:
            self.groq_llm = None

    def generate(self, system_prompt: str, user_prompt: str, fallback_text: str) -> str:
        if self.provider == "OLLAMA":
            text = self._generate_with_ollama(system_prompt, user_prompt)
            return text if text else fallback_text

        if self.provider == "GROQ":
            text = self._generate_with_groq(system_prompt, user_prompt)
            return text if text else fallback_text

        return fallback_text

    def _generate_with_ollama(self, system_prompt: str, user_prompt: str) -> str:
        if self.ollama_llm is None:
            return ""

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            response = self.ollama_llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
            return str(response.content).strip()
        except Exception:
            logger.exception("OLLAMA generation failed.")
            return ""

    def _generate_with_groq(self, system_prompt: str, user_prompt: str) -> str:
        if self.groq_llm is not None:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage

                response = self.groq_llm.invoke(
                    [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_prompt),
                    ]
                )
                return str(response.content).strip()
            except Exception:
                logger.exception("GROQ generation through langchain_groq failed.")

        if not self.groq_api_key:
            return ""

        payload = json.dumps(
            {
                "model": self.groq_model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
        ).encode("utf-8")

        api_request = request.Request(
            url="https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(api_request, timeout=45) as response:
                body = response.read().decode("utf-8")
            decoded = json.loads(body)
            message = decoded.get("choices", [{}])[0].get("message", {})
            return str(message.get("content", "")).strip()
        except (error.HTTPError, error.URLError, TimeoutError, ValueError):
            logger.exception("GROQ generation via HTTP API failed.")
            return ""
        except Exception:
            logger.exception("Unexpected GROQ generation failure.")
            return ""


@lru_cache(maxsize=1)
def get_free_llm() -> FreeMedicalLLM:
    return FreeMedicalLLM()
