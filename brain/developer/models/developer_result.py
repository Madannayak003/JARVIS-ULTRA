"""
Developer Result Model
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DeveloperResult:
    """
    Final result returned by Developer.
    """

    success: bool = False

    message: str = ""

    project_path: Path | None = None