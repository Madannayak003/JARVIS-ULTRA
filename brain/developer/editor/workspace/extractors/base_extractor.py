"""
JARVIS PRO
Developer Editor

Base Extractor
"""

from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """
    Base class for all code extractors.
    """

    @abstractmethod
    def extract(
        self,
        request: str,
        edit_type: str,
        content: str,
    ) -> str:
        """
        Extract the relevant code snippet.
        """
        raise NotImplementedError