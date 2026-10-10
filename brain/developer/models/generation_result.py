"""
Generation Result Model
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class GenerationResult:
    """
    Output produced by the Generator.
    """

    success: bool = False

    files: dict[str, str] = field(default_factory=dict)

    message: str = ""