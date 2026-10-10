"""
JARVIS PRO
Developer Analyzer

Base Detector
"""

from abc import ABC, abstractmethod
import re

from brain.developer.models.analysis_context import AnalysisContext


class BaseDetector(ABC):
    """
    Base class for all detectors.
    """

    @abstractmethod
    def detect(self, context: AnalysisContext):
        pass

    def create_context(self, text: str) -> AnalysisContext:
        """
        Create an AnalysisContext from raw user input.
        """

        normalized = self.normalize(text)

        tokens = normalized.split()

        return AnalysisContext(
            raw_text=text,
            normalized_text=normalized,
            tokens=tokens,
        )

    def normalize(self, text: str) -> str:
        """
        Normalize user input.
        """

        text = text.lower()

        replacements = {
            "c++": "cpp",
            "c#": "csharp",
            ".net": "dotnet",

            "next.js": "nextjs",
            "react.js": "reactjs",
            "vue.js": "vuejs",
            "express.js": "expressjs",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()