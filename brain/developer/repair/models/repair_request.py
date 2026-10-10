"""
JARVIS PRO
Developer Repair

Repair Request
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class RepairRequest:
    """
    Represents a request to repair
    an incomplete generated project.
    """

    missing_files: list[str] = field(default_factory=list)

    missing_folders: list[str] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)