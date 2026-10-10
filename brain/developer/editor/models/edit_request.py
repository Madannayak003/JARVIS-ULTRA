"""
JARVIS PRO
Developer Editor

Edit Request
"""

from dataclasses import dataclass, field

from brain.developer.editor.models.project_index import (
    ProjectIndex,
)


@dataclass
class EditRequest:
    """
    Represents a user's edit request.
    """

    # * -------------------------------------

    user_request: str = ""

    edit_type: str = ""

    project_path: str = ""

    # * -------------------------------------

    project_index: ProjectIndex | None = None

    # * -------------------------------------

    target_files: list[str] = field(
        default_factory=list,
    )

    file_contents: dict[str, str] = field(
        default_factory=dict,
    )

    instructions: list[str] = field(
        default_factory=list,
    )
    
    implementation_steps: list[str] = field(
        default_factory=list
    )
    
    primary_files: list[str] = field(
    default_factory=list
    )

    dependent_files: list[str] = field(
        default_factory=list
    )