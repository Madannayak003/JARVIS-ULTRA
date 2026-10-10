"""
Workspace Result Model
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class WorkspaceResult:
    """
    Result of workspace operations.
    """

    success: bool = False

    project_path: Path | None = None