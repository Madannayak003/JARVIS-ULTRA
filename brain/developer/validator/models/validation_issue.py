"""
JARVIS PRO
Developer Validator

Validation Issue
"""

from dataclasses import dataclass, field

from brain.developer.validator.models.validation_level import (
    ValidationLevel,
)


@dataclass(slots=True)
class ValidationIssue:
    """
    Represents a single validation issue
    found during project validation.
    """

    # * ---------------------------------------
    # * Issue Information
    # * ---------------------------------------

    level: ValidationLevel

    validator: str

    message: str

    # * ---------------------------------------
    # * Optional Context
    # * ---------------------------------------

    file: str = ""

    expected: str = ""

    actual: str = ""

    suggestion: str = ""

    # * ---------------------------------------
    # * Extra Metadata
    # * ---------------------------------------

    metadata: dict = field(default_factory=dict)