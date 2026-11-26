"""
ml/llm/provider.py — Abstract LLM provider interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class LLMProvider(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Generate a completion for the given prompt."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is reachable and ready."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...


class NoOpLLMProvider(LLMProvider):
    """Fallback provider when LLM_PROVIDER=none — always returns empty string."""

    def generate(self, prompt: str, **kwargs) -> str:
        return ""

    def is_available(self) -> bool:
        return False

    @property
    def name(self) -> str:
        return "none"
