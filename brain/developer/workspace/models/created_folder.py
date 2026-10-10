"""
JARVIS PRO
Developer Workspace

Created Folder
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class CreatedFolder:
    """
    Represents one folder created
    by the Workspace Engine.
    """

    # * ---------------------------------------
    # * Folder Information
    # * ---------------------------------------

    name: str

    path: str

    # * ---------------------------------------
    # * Status
    # * ---------------------------------------

    created: bool = False

    already_exists: bool = False

    # * ---------------------------------------
    # * Metadata
    # * ---------------------------------------

    metadata: dict = field(default_factory=dict)