"""
JARVIS PRO
Developer Memory

Dependency Record
"""

from dataclasses import dataclass, field


@dataclass
class DependencyRecord:
    """
    Represents the dependency
    relationship between files.
    """

    source: str = ""

    target: str = ""

    dependency_type: str = ""

    symbols: list[str] = field(
        default_factory=list,
    )