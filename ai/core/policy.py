"""
JARVIS PRO
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
            "ollama",
        ],

        # * --------------------------------------------------
        # * Developer Mode
        # * --------------------------------------------------

        "developer": [
            "gemini",
            "grok",
            "openai",
            "ollama",
        ],

        # * --------------------------------------------------
        # * Editing
        # * --------------------------------------------------

        "editing": [
            "gemini",
            "grok",
            "openai",
            "ollama",
        ],

        # * --------------------------------------------------
        # * Repair
        # * --------------------------------------------------

        "repair": [
            "gemini",
            "grok",
            "openai",
            "ollama",
        ],

        # * --------------------------------------------------
        # * Reasoning
        # * --------------------------------------------------

        "reasoning": [
            "gemini",
            "grok",
            "openai",
            "ollama",
        ],

        # * --------------------------------------------------
        # * Conversation
        # * --------------------------------------------------

        "conversation": [
            "gemini",
            "grok",
            "openai",
            "ollama",
        ],

        # * --------------------------------------------------
        # * Planning
        # * --------------------------------------------------

        "planning": [
            "gemini",
            "grok",
            "openai",
            "ollama",
        ],

        # * --------------------------------------------------
        # * Memory
        # * --------------------------------------------------

        "memory": [
            "gemini",
            "grok",
            "openai",
            "ollama",
        ],

        # * --------------------------------------------------
        # * Fast
        # * --------------------------------------------------

        "fast": [
            "gemini",
            "grok",
            "openai",
            "ollama",
        ],

        # * --------------------------------------------------
        # * Offline
        # * --------------------------------------------------

        "offline": [
            "ollama",
        ],
        
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
                "ollama",
            ],
        )
