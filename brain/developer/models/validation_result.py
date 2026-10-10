"""
Validation Result Model
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class ValidationResult:
    """
    Validation report.
    """

    success: bool = False

    errors: list[str] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)