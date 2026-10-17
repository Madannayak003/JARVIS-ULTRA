"""
JARVIS ULTRA
AI Core - Model Policy

Defines which AI capabilities should prefer
which providers/models.

Policy decides preference.
Router decides availability and fallback.
"""

from typing import Dict, List


class AIModelPolicy:
    """
    Central model-selection policy.
    """

    # * ======================================================
    # * Provider Preference
    # * ======================================================

    PROVIDER_PREFERENCES: Dict[str, List[str]] = {

        # * --------------------------------------------------
        # * Coding
        # * --------------------------------------------------

        "coding": [
            "gemini",
            "grok",
            "openai",
        ],

        # * --------------------------------------------------
        # * Developer Mode
        # * --------------------------------------------------

        "developer": [
            "gemini",
            "grok",
            "openai",
        ],

        # * --------------------------------------------------
        # * Editing
        # * --------------------------------------------------

        "editing": [
            "gemini",
            "grok",
            "openai",
        ],

        # * --------------------------------------------------
        # * Repair
        # * --------------------------------------------------

        "repair": [
            "gemini",
            "grok",
            "openai",
        ],

        # * --------------------------------------------------
        # * Reasoning
        # * --------------------------------------------------

        "reasoning": [
            "gemini",
            "grok",
            "openai",
        ],

        # * --------------------------------------------------
        # * Conversation
        # * --------------------------------------------------

        "conversation": [
            "gemini",
            "grok",
            "openai",
        ],

        # * --------------------------------------------------
        # * Planning
        # * --------------------------------------------------

        "planning": [
            "gemini",
            "grok",
            "openai",
        ],

        # * --------------------------------------------------
        # * Memory
        # * --------------------------------------------------

        "memory": [
            "gemini",
            "grok",
            "openai",
        ],

        # * --------------------------------------------------
        # * Fast
        # * --------------------------------------------------

        "fast": [
            "gemini",
            "grok",
            "openai",
        ],

        # * --------------------------------------------------
        # * --------------------------------------------------
        # * Screen Vision
        # * --------------------------------------------------

        "screen_vision": [
            "gemini",
            "openai",
        ],
    }

    # * ======================================================
    # * Get Provider Preference
    # * ======================================================

    @classmethod
    def providers_for(
        cls,
        capability: str,
    ) -> List[str]:

        capability = (
            capability
            .strip()
            .lower()
        )

        return cls.PROVIDER_PREFERENCES.get(
            capability,
            [
                "gemini",
                "grok",
                "openai",
            ],
        )
