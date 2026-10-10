"""
JARVIS PRO
Developer Workspace

Workspace Result
"""

from dataclasses import dataclass, field

from brain.developer.workspace.models.created_file import CreatedFile
from brain.developer.workspace.models.created_folder import CreatedFolder


@dataclass(slots=True)
class WorkspaceResult:
    """
    Represents the final result of creating
    a project on disk.
    """

    # * ---------------------------------------
    # * Overall Status
    # * ---------------------------------------

    success: bool = False

    # * ---------------------------------------
    # * Project Information
    # * ---------------------------------------

    project_name: str = ""

    project_path: str = ""

    # * ---------------------------------------
    # * Created Resources
    # * ---------------------------------------

    folders: list[CreatedFolder] = field(default_factory=list)

    files: list[CreatedFile] = field(default_factory=list)

    # * ---------------------------------------
    # * Statistics
    # * ---------------------------------------

    folder_count: int = 0

    file_count: int = 0

    bytes_written: int = 0

    # * ---------------------------------------
    # ! Errors
    # * ---------------------------------------

    errors: list[str] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)

    # * ---------------------------------------
    # * Metadata
    # * ---------------------------------------

    metadata: dict = field(default_factory=dict)