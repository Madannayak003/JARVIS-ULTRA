"""
JARVIS PRO
Developer Editor

Edit Plan
"""

from dataclasses import dataclass, field

from brain.developer.editor.models.edit_request import (
    EditRequest,
)


@dataclass
class EditPlan:
    """
    Represents the execution plan generated
    by the Edit Planner.
    """
    
    # * -------------------------------------
    # * Original Request
    # * -------------------------------------

    request: EditRequest | None = None

    # * -------------------------------------
    # * Files
    # * -------------------------------------

    primary_files: list[str] = field(
        default_factory=list,
    )

    dependent_files: list[str] = field(
        default_factory=list,
    )

    target_files: list[str] = field(
        default_factory=list,
    )

    # * -------------------------------------
    # * Execution
    # * -------------------------------------

    implementation_steps: list[str] = field(
        default_factory=list,
    )

    validation_steps: list[str] = field(
        default_factory=list,
    )

    # * -------------------------------------
    # * Metadata
    # * -------------------------------------

    estimated_changes: int = 0

    requires_tests: bool = False