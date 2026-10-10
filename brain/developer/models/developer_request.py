"""
Developer Request Model
"""

from dataclasses import dataclass


@dataclass(slots=True)
class DeveloperRequest:
    """
    Represents a request entering the Developer subsystem.
    """

    text: str