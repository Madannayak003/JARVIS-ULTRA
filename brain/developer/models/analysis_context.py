"""
JARVIS PRO
Developer

Analysis Context
"""

from dataclasses import dataclass, field


@dataclass
class AnalysisContext:
    """
    Shared analysis context for all detectors.
    """

    raw_text: str

    normalized_text: str

    tokens: list[str] = field(default_factory=list)