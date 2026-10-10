"""
JARVIS PRO
Developer Editor

Base Provider
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """
    Base class for every editor provider.
    """

    @abstractmethod
    def generate(
        self,
        prompt: Any,
    ) -> str:
        """
        Generate a response from an AI provider.
        """
        raise NotImplementedError