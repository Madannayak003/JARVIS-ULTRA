"""
JARVIS ULTRA
AI Core - AI Selection Commands

Converts natural AI selection commands into
AI preference changes.

Examples:

    use Gemini
    Legacy provider-selection commands are no longer supported.
"""

import re


class AICommandHandler:

    PROVIDER_ALIASES = {

        "gemini": "gemini",

        "google": "gemini",

    }

    # * ======================================================
    # * Handle Command
    # * ======================================================

    @classmethod
    def handle(
        cls,
        command: str,
        preference,
    ):

        if not command:

            return None

        command = command.strip().lower()

        # * --------------------------------------------------
        # * Use provider
        # * --------------------------------------------------

        match = re.fullmatch(
            r"use\s+(gemini|google)",
            command,
        )

        if match:

            requested = match.group(1)

            provider = cls.PROVIDER_ALIASES[
                requested
            ]

            preference.set_provider(
                provider
            )

            return {
                "handled": True,
                "action": "provider",
                "provider": provider,
                "message": (
                    f"AI provider set to {provider}."
                ),
            }

        return None
