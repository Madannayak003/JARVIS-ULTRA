"""
JARVIS PRO HUD

Visual interface for JARVIS PRO.

The HUD is a display layer only.
It does not contain JARVIS intelligence or command logic.
"""

from .adapter import HUDAdapter

__all__ = [
    "HUDAdapter",
]