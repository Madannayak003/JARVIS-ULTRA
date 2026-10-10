"""
JARVIS PRO
Developer Generator

Generated File
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class GeneratedFile:
    """
    Represents one generated file.
    """

    # * ---------------------------------------
    # * File Information
    # * ---------------------------------------

    name: str

    path: str

    extension: str

    # * ---------------------------------------
    # * Content
    # * ---------------------------------------

    content: str = ""

    # * ---------------------------------------
    # * Language Information
    # * ---------------------------------------

    language: str = ""

    markdown_language: str = ""

    # * ---------------------------------------
    # * File Statistics
    # * ---------------------------------------

    size: int = 0

    line_count: int = 0

    is_empty: bool = False

    # * ---------------------------------------
    # * Metadata
    # * ---------------------------------------

    encoding: str = "utf-8"

    executable: bool = False

    generated: bool = True

    metadata: dict = field(default_factory=dict)