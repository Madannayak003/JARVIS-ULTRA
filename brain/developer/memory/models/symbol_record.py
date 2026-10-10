"""
JARVIS PRO
Developer Memory

Symbol Record
"""

from dataclasses import dataclass, field


@dataclass
class SymbolRecord:
    """
    Stores information about
    a symbol inside the project.
    """

    name: str = ""

    symbol_type: str = ""

    file: str = ""

    line: int = 0

    references: list[str] = field(
        default_factory=list,
    )

    documentation: str = ""