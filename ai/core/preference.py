"""
JARVIS ULTRA
AI Core - AI Preference

Stores the user's temporary AI provider/model preference.

Examples:
    use Gemini
    Legacy provider settings are normalized to Gemini.
"""


from config.settings import (
    get_ai_provider_setting,
    set_ai_provider_setting,
)


class AIPreference:

    PROVIDER_MODES = ("gemini",)

    def __init__(self):

        self.provider = get_ai_provider_setting().lower()
        self.model = None

    # * ======================================================
    # * Set Provider
    # * ======================================================

    def set_provider(
        self,
        provider: str,
    ):

        normalized = provider.strip().lower()
        if normalized in {"auto", "google", "grok", "xai", "gpt", "openai"}:
            normalized = "gemini"
        if normalized not in self.PROVIDER_MODES:
            raise ValueError(f"Unsupported AI provider: {provider}")

        self.provider = normalized

        self.model = None
        set_ai_provider_setting(normalized)

    # * ======================================================
    # * Set Model
    # * ======================================================

    def set_model(
        self,
        model: str,
    ):

        self.model = (
            model.strip()
        )

        self.provider = None

    # * ======================================================
    # * Automatic Mode
    # * ======================================================

    def clear(self):

        self.provider = "gemini"
        self.model = None
        set_ai_provider_setting("gemini")

    @property
    def mode(self) -> str:
        return self.provider

    # * ======================================================
    # * State
    # * ======================================================

    @property
    def is_manual(self) -> bool:

        return (
            self.provider is not None
            or self.model is not None
        )

    # * ======================================================
    # * Description
    # * ======================================================

    def describe(self) -> str:

        if self.model:

            return (
                f"model:{self.model}"
            )

        if self.provider:

            return (
                f"provider:{self.provider}"
            )

        return "provider:gemini"
