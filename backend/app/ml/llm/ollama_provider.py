"""
ml/llm/ollama_provider.py — Ollama LLM provider using HTTP API.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.ml.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Calls a locally running Ollama instance via its REST API.
    Uses /api/generate (non-streaming) for simplicity and reliability.
    """

    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        model: str = settings.OLLAMA_MODEL,
        timeout: int = settings.LLM_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    @property
    def name(self) -> str:
        return f"ollama:{self.model}"

    def is_available(self) -> bool:
        """Ping Ollama health endpoint."""
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """
        Call Ollama /api/generate and return the generated text.

        :raises RuntimeError: If the HTTP call fails.
        """
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama HTTP error {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """
        Call Ollama /api/chat with a messages list.
        Each message: {"role": "user"|"assistant"|"system", "content": "..."}
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
        except Exception as exc:
            raise RuntimeError(f"Ollama chat failed: {exc}") from exc


ollama_provider = OllamaProvider()
