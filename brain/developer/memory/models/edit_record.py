"""
JARVIS PRO
Developer Memory

Edit Record
"""

from dataclasses import dataclass, field


@dataclass
class EditRecord:
    """
    Stores a single edit
    performed by the editor.
    """

    request: str = ""

    edit_type: str = ""

    files: list[str] = field(
        default_factory=list,
    )

    timestamp: str = ""

    success: bool = False

    notes: str = ""