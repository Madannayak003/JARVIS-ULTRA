"""
JARVIS PRO
Developer Memory

Session State
"""

from dataclasses import dataclass, field


@dataclass
class SessionState:
    """
    Stores the current
    developer session.
    """

    project_path: str = ""

    current_file: str = ""

    open_files: list[str] = field(
        default_factory=list,
    )

    recent_requests: list[str] = field(
        default_factory=list,
    )

    recent_files: list[str] = field(
        default_factory=list,
    )

    last_updated: str = ""