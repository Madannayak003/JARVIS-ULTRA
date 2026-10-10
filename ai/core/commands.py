"""
JARVIS PRO
AI Core - AI Selection Commands

Converts natural AI selection commands into
AI preference changes.

Examples:

    use Gemini
    use GPT
    use OpenAI
    use Ollama
    use Qwen
    auto mode
"""

import re


class AICommandHandler:

    PROVIDER_ALIASES = {

        "gemini": "gemini",

        "google": "gemini",

        "gpt": "openai",

        "openai": "openai",

        "ollama": "ollama",

        "qwen": "ollama",

        "grok": "grok",

        "xai": "grok",

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
        # * Automatic mode
        # * --------------------------------------------------

        if command in [

            "auto",

            "auto mode",

            "automatic mode",

            "use auto",

            "use automatic mode",

        ]:

            preference.clear()

            return {
                "handled": True,
                "action": "auto",
                "message": (
                    "Automatic AI selection enabled."
                ),
            }

        # * --------------------------------------------------
        # * Use provider
        # * --------------------------------------------------

        match = re.fullmatch(
            r"use\s+(gemini|google|gpt|openai|ollama|qwen|grok|xai)",
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
