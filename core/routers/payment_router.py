"""Fast routes for the separate user-driven Payment skill."""

from __future__ import annotations

import re


def payment_route(command):
    if not command:
        return None
    command = str(command).strip()
    if command.casefold() == "make payment":
        return [{"action": "make_payment"}]
    match = re.fullmatch(
        r"make\s+payment\s+(?:using|with)\s+(.+)",
        command,
        flags=re.IGNORECASE,
    )
    if match:
        app = match.group(1).strip()
        if app:
            return [{"action": "make_payment", "payment_app": app}]
    return None
