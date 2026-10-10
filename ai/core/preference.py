"""
JARVIS PRO
AI Core - AI Preference

Stores the user's temporary AI provider/model preference.

Examples:
    use Gemini
    use GPT
    use Ollama
    use Qwen
    auto mode
"""


from config.settings import (
    get_ai_provider_setting,
    set_ai_provider_setting,
)


class AIPreference:

    PROVIDER_MODES = ("auto", "ollama", "gemini", "grok", "openai")

    def __init__(self):

        persisted = get_ai_provider_setting().lower()
        self.provider = None if persisted == "auto" else persisted
        self.model = None

    # * ======================================================
    # * Set Provider
    # * ======================================================

    def set_provider(
        self,
        provider: str,
    ):

        normalized = provider.strip().lower()
        if normalized not in self.PROVIDER_MODES:
            raise ValueError(f"Unsupported AI provider: {provider}")

        self.provider = None if normalized == "auto" else normalized

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

        self.provider = None
        self.model = None
        set_ai_provider_setting("auto")

    @property
    def mode(self) -> str:
        return self.provider or "auto"

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

        return "auto"
