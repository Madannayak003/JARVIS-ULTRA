"""
JARVIS PRO
Developer Memory

Style Profile
"""

from dataclasses import dataclass, field


@dataclass
class StyleProfile:
    """
    Stores the coding style
    detected for a project.
    """

    indentation: int = 4

    quote_style: str = "double"

    naming_style: str = "snake_case"

    line_length: int = 88

    docstrings: bool = True

    type_hints: bool = True

    imports_sorted: bool = False

    trailing_newline: bool = True

    extra: dict = field(
        default_factory=dict,
    )