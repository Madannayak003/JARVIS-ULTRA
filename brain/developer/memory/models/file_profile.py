"""
JARVIS PRO
Developer Memory

File Profile
"""

from dataclasses import dataclass, field


@dataclass
class FileProfile:
    """
    Stores metadata for
    a single project file.
    """

    path: str = ""

    language: str = ""

    checksum: str = ""

    functions: list[str] = field(
        default_factory=list,
    )

    classes: list[str] = field(
        default_factory=list,
    )

    imports: list[str] = field(
        default_factory=list,
    )

    last_modified: str = ""