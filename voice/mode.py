"""
JARVIS PRO
Voice Mode Selector

This module only detects network availability.

IMPORTANT:
It does NOT import:
    voice.manager
    voice.online_edge
    voice.offline.*
    core.listener
"""

import requests


def internet_available(timeout=2):
    """
    Return True when Internet connectivity is available.
    """

    try:
        requests.get(
            "https://www.google.com",
            timeout=timeout,
        )

        return True

    except Exception:

        return False


def get_mode():
    """
    Return the voice operating mode.

    Returns:
        "online"
        "offline"
    """

    if internet_available():

        return "online"

    return "offline"