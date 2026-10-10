"""
JARVIS PRO
Developer Validator

Validation Result
"""

from dataclasses import dataclass, field

from brain.developer.validator.models.validation_issue import (
    ValidationIssue,
)


@dataclass(slots=True)
class ValidationResult:
    """
    Represents the complete validation report
    for a generated project.
    """

    # * ---------------------------------------
    # * Overall Status
    # * ---------------------------------------

    valid: bool = True

    score: int = 100

    grade: str = "A+"

    # * ---------------------------------------
    # * Validation Issues
    # * ---------------------------------------

    issues: list[ValidationIssue] = field(default_factory=list)

    # * ---------------------------------------
    # * Statistics
    # * ---------------------------------------

    total_checks: int = 0

    passed_checks: int = 0

    failed_checks: int = 0

    warning_count: int = 0

    error_count: int = 0

    critical_count: int = 0

    # * ---------------------------------------
    # * Validator Statistics
    # * ---------------------------------------

    validated_files: int = 0

    validated_folders: int = 0

    validated_dependencies: int = 0

    execution_time_ms: float = 0.0

    # * ---------------------------------------
    # * Summary
    # * ---------------------------------------

    summary: str = ""

    # * ---------------------------------------
    # * Extra Metadata
    # * ---------------------------------------

    metadata: dict = field(default_factory=dict)
    