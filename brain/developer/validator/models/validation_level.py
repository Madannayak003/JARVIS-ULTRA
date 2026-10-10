"""
JARVIS PRO
Developer Validator

Validation Level
"""

from enum import Enum, auto


class ValidationLevel(Enum):
    """
    Severity level of a validation issue.
    """

    INFO = auto()

    WARNING = auto()

    ERROR = auto()

    CRITICAL = auto()