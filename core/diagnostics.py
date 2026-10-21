"""Small opt-in switch for verbose runtime diagnostics.

Normal operation keeps the terminal focused on useful operational messages.
Set ``JARVIS_DEBUG=1`` when provider, streaming, or TTS internals are needed.
This deliberately avoids introducing a second logging framework.
"""

from __future__ import annotations

import os
import sys


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


def status_print(message: str, *, debug_message: str | None = None) -> None:
    """Print a compact robot-prefixed status, or detailed text in debug mode."""

    if debug_enabled():
        print(debug_message or message)
        return

    stream = sys.stdout
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass
    print("🤖", message)

