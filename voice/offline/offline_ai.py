"""
JARVIS PRO
Offline AI Brain

Completely isolated offline AI layer.

Pipeline:

Offline STT
    ↓
ContextBuilder
    ↓
PromptBuilder
    ↓
Ollama
    ↓
Offline TTS

IMPORTANT:
This module never uses:
- OpenAI
- Gemini
- Edge TTS
- Google STT
- Internet
- voice.manager
"""

import time

from ai.core.schemas import AIRequest
from ai.providers.ollama import OllamaProvider
from brain.profile_manager import ProfileManager
from brain.conversation_manager import ConversationManager
from brain.context_builder import ContextBuilder
from brain.prompt_builder import PromptBuilder
from config.environment import get_env
from config.settings import get_assistant_display_name


# * =========================================================
# * Configuration
# * =========================================================

OLLAMA_URL = get_env(
    "OLLAMA_API_URL",
    "http://127.0.0.1:11434/api/generate",
)

OLLAMA_MODEL = "jarvis"

OLLAMA_TIMEOUT = 120

# * =========================================================
# * Offline Voice Instructions
# * =========================================================

def _offline_voice_instructions() -> str:
    return f"""
You are {get_assistant_display_name()} operating in OFFLINE VOICE MODE.

You are speaking directly to the user.

Response rules:
- Give short, natural spoken answers.
- Normally answer in 1 to 3 sentences.
- Prefer 1 or 2 sentences for simple questions.
- Do not give long explanations unless the user explicitly asks for details.
- Do not use Markdown headings.
- Do not use bullet points unless specifically requested.
- Do not use tables.
- Do not repeat the user's question.
- Speak naturally and conversationally.
- Use the user's profile, conversation context, project context, and memories when relevant.
- Never invent information.
"""


# * =========================================================
# * Offline Brain
# * =========================================================

class OfflineAI:

    def __init__(self, provider=None):

        print("[OFFLINE AI] Initializing...")

        # * -------------------------------------------------
        # * Existing Stage 4 components
        # * -------------------------------------------------

        self.profile = ProfileManager()

        self.conversation = ConversationManager()

        self.context_builder = ContextBuilder(
            profile_manager=self.profile,
            conversation_manager=self.conversation,
            memory_manager=None,
            planner=None,
        )

        self.prompt_builder = PromptBuilder()

        # * Use the shared Ollama provider contract while forcing the provider
        # * to remain local. The model can still be selected explicitly through
        # * OLLAMA_MODEL, with the existing offline ``jarvis`` default retained.
        self.model = get_env("OLLAMA_MODEL", OLLAMA_MODEL)
        self.provider = provider or OllamaProvider(
            model=self.model,
            url=OLLAMA_URL,
        )
        self.ready = False
        self.last_error = ""
        self._initialize_provider()

        print("[OFFLINE AI] Stage 4 context ready.")

    def _initialize_provider(self):
        """Check the local Ollama service once; never probe the internet."""

        try:
            self.ready = bool(self.provider.is_available())
        except Exception as error:
            self.ready = False
            self.last_error = str(error)

        if self.ready:
            print(f"[OFFLINE AI] Ollama ready ({self.model}).")
        else:
            self.last_error = (
                self.last_error
                or "Ollama is not reachable at the configured local URL."
            )
            print(f"[OFFLINE AI ERROR] {self.last_error}")

    # * =====================================================
    # * Ollama
    # * =====================================================

    def _ollama(self, prompt):
        started = time.perf_counter()
        response = self.provider.generate(
            AIRequest(
                prompt=prompt,
                capability="conversation",
                model=self.model,
                metadata={"offline": True},
            )
        )

        if not response.success:
            self.ready = False
            self.last_error = response.error or "Ollama generation failed."
            print(f"[OFFLINE AI ERROR] {self.last_error}")
            return None

        print(
            f"[OFFLINE AI] Ollama response: "
            f"{time.perf_counter() - started:.2f}s"
        )
        return response.text.strip()

    # * =====================================================
    # * Ask
    # * =====================================================

    def ask(self, user_input):

        if not user_input:

            return None

        if not self.ready:
            print(
                "[OFFLINE AI ERROR] "
                f"Ollama unavailable: {self.last_error}"
            )
            return None

        user_input = str(
            user_input
        ).strip()

        if not user_input:

            return None

        print(
            "[OFFLINE AI] Building context..."
        )

        # * -------------------------------------------------
        # * Build existing Stage 4 context
        # * -------------------------------------------------

        context = self.context_builder.build(
            user_input
        )

        # * -------------------------------------------------
        # * Build existing Stage 4 prompt
        # * -------------------------------------------------

        base_prompt = self.prompt_builder.build(
            context
        )

        prompt = (
            base_prompt
            + "\n\n"
            + _offline_voice_instructions()
        )

        print(
            "[OFFLINE AI] Thinking..."
        )

        # * -------------------------------------------------
        # * Local Ollama
        # * -------------------------------------------------

        response = self._ollama(
            prompt
        )

        if not response:

            return None

        # * -------------------------------------------------
        # * Save conversation
        # * -------------------------------------------------

        self.conversation.add_user_message(
            user_input
        )

        self.conversation.add_assistant_message(
            response
        )

        return response


# * =========================================================
# * Singleton
# * =========================================================

_ai = None


def get_ai():

    global _ai

    if _ai is None:

        _ai = OfflineAI()

    return _ai


# * =========================================================
# * Simple API
# * =========================================================

def ask(user_input):

    return get_ai().ask(
        user_input
    )
