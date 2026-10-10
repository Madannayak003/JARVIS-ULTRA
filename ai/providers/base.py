"""
JARVIS PRO
AI Core - Base Provider

Common interface implemented by:
- OllamaProvider
- GeminiProvider
- OpenAIProvider
- GrokProvider
"""

from abc import ABC, abstractmethod
from typing import Iterator

from ai.core.schemas import (
    AIRequest,
    AIResponse,
    AIStreamChunk,
)


class AIProvider(ABC):
    """
    Base interface for all JARVIS AI providers.
    """

    # * ======================================================
    # * Provider Information
    # * ======================================================

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return provider name.

        Example:
            ollama
            gemini
            openai
            grok
        """
        pass

    # * ======================================================
    # * Availability
    # * ======================================================

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check whether this provider is currently available.
        """
        pass

    # * ======================================================
    # * Generation
    # * ======================================================

    @abstractmethod
    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        """
        Generate a complete AI response.
        """
        pass

    # * ======================================================
    # * Streaming
    # * ======================================================

    @abstractmethod
    def stream(
        self,
        request: AIRequest,
    ) -> Iterator[AIStreamChunk]:
        """
        Stream an AI response.
        """
        pass
