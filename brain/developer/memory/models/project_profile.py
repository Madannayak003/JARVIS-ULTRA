"""
JARVIS PRO
Developer Memory

Project Profile
"""

from dataclasses import dataclass, field


@dataclass
class ProjectProfile:
    """
    Stores information about
    the current project.
    """

    name: str = ""

    path: str = ""

    language: str = ""

    framework: str = ""

    project_type: str = ""

    entry_file: str = ""

    files: list[str] = field(
        default_factory=list,
    )

    dependencies: list[str] = field(
        default_factory=list,
    )

    created_at: str = ""

    updated_at: str = ""