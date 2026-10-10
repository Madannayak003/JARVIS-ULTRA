"""
JARVIS PRO
Developer Prompt Builder

Base Builder
"""

from abc import ABC, abstractmethod

from brain.developer.prompt_builder.models.prompt_context import PromptContext


class BaseBuilder(ABC):
    """
    Base class for all prompt builders.
    """

    @abstractmethod
    def build(self, context: PromptContext):
        """
        Build one part of the final prompt.
        """
        pass