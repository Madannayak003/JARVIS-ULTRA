"""
JARVIS PRO
Developer Editor

Edit Result
"""

from dataclasses import dataclass, field

from brain.developer.editor.models.patch import Patch


@dataclass
class EditResult:

    success: bool = False

    message: str = ""

    patches: list[Patch] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )