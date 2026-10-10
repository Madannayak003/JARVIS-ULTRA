"""
JARVIS PRO
Developer Repair

Repair Result
"""

from dataclasses import dataclass, field

from brain.developer.generator.models.generated_file import (
    GeneratedFile,
)


@dataclass(slots=True)
class RepairResult:
    """
    Represents the result of repairing
    an incomplete generated project.
    """

    # * ---------------------------------------
    # * Status
    # * ---------------------------------------

    success: bool = False

    # * ---------------------------------------
    # * Generated Files
    # * ---------------------------------------

    files: list[GeneratedFile] = field(default_factory=list)

    # * ---------------------------------------
    # * Statistics
    # * ---------------------------------------

    repaired_files: int = 0

    # * ---------------------------------------
    # ! Errors
    # * ---------------------------------------

    errors: list[str] = field(default_factory=list)