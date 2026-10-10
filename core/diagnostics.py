"""Small opt-in switch for verbose runtime diagnostics.

Normal operation keeps the terminal focused on useful operational messages.
Set ``JARVIS_DEBUG=1`` when provider, streaming, or TTS internals are needed.
This deliberately avoids introducing a second logging framework.
"""

from __future__ import annotations

import os


def debug_enabled() -> bool:
    value = os.getenv("JARVIS_DEBUG", "0")
    return str(value).strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
        "debug",
    }


def debug_print(*args, **kwargs):
    """Print diagnostics only when explicitly enabled."""

    if debug_enabled():
        print(*args, **kwargs)

