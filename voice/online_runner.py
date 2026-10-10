"""
JARVIS PRO
Online Voice Runner

This is only a wrapper around the existing online JARVIS.

IMPORTANT:
Do not modify the existing online voice architecture.
"""

from core.assistant import run as run_online
from config.settings import get_assistant_display_name
from core.diagnostics import debug_print


def run():
    """
    Start the existing online JARVIS.
    """

    debug_print(
        f"[ONLINE VOICE] Starting existing online {get_assistant_display_name()}..."
    )

    return run_online()
