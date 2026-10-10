"""
JARVIS PRO
Developer Editor

Patch
"""

from dataclasses import dataclass


@dataclass
class Patch:
    """
    Represents one modified file returned
    by the LLM.
    """

    path: str = ""

    language: str = ""

    content: str = ""

    is_new_file: bool = False

    is_deleted: bool = False