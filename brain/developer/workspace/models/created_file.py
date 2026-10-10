"""
JARVIS PRO
Developer Workspace

Created File
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class CreatedFile:
    """
    Represents one file created
    by the Workspace Engine.
    """

    # * ---------------------------------------
    # * File Information
    # * ---------------------------------------

    name: str

    path: str

    extension: str

    # * ---------------------------------------
    # * Statistics
    # * ---------------------------------------

    size: int = 0

    encoding: str = "utf-8"

    # * ---------------------------------------
    # * Status
    # * ---------------------------------------

    created: bool = False

    overwritten: bool = False

    # * ---------------------------------------
    # * Metadata
    # * ---------------------------------------

    metadata: dict = field(default_factory=dict)