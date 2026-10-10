"""
JARVIS PRO
Developer Memory

Memory Record
"""

from dataclasses import dataclass, field


@dataclass
class MemoryRecord:
    """
    Base memory object used throughout
    the Developer Memory system.
    """

    # * -------------------------------------
    # * Identity
    # * -------------------------------------

    key: str = ""

    category: str = ""

    # * -------------------------------------
    # * Stored Data
    # * -------------------------------------

    value: dict = field(
        default_factory=dict,
    )

    # * -------------------------------------
    # * Metadata
    # * -------------------------------------

    created_at: str = ""

    updated_at: str = ""

    access_count: int = 0

    last_accessed: str = ""

    tags: list[str] = field(
        default_factory=list,
    )