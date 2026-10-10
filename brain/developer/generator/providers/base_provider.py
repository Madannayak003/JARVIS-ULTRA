"""
JARVIS PRO
Developer Generator

Base Provider
"""

from abc import ABC, abstractmethod

from brain.developer.prompt_builder.models.prompt_result import PromptResult


class BaseProvider(ABC):
    """
    Base class for all AI providers.
    """

    @abstractmethod
    def generate(
        self,
        prompt: PromptResult,
    ) -> str:
        """
        Generate a raw response from the LLM.

        Returns:
            Raw text response.
        """
        pass