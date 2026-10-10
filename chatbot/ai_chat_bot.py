"""
JARVIS PRO
Standalone AI Chatbot

This chatbot is completely independent from the main JARVIS system.

It does NOT use:
- brain
- core.dispatcher
- JARVIS conversation manager
- JARVIS memory
- JARVIS prompt builder
- ai.core.service
- ai.providers.gemini
- Agent
"""

from dataclasses import dataclass
from typing import Iterator, Optional

from google import genai
from google.genai import types

from chatbot.ai_chat_session import chat_sessions
from config.environment import get_env


DEFAULT_MODEL = "gemini-3.6-flash"

SUPPORTED_MODELS = (
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
)

CHATBOT_SYSTEM_PROMPT = """
You are an independent AI chatbot.

You are not JARVIS and you are not connected to the JARVIS
desktop assistant.

You do not have access to:
- the user's computer
- JARVIS commands
- JARVIS memory
- JARVIS skills
- JARVIS system state
- JARVIS Agent

Answer the user naturally and helpfully.

Only use information contained in the current chatbot conversation
or information explicitly provided in the current request.

Do not claim to have performed actions on the user's computer.
""".strip()


@dataclass
class ChatStreamChunk:
    text: str = ""
    model: str = DEFAULT_MODEL
    done: bool = False
    error: Optional[str] = None


class AIChatBot:
    """
    Completely standalone Gemini chatbot.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        self.api_key = api_key or get_env("GEMINI_API_KEY")

        self.model = model
        self._client = None
        
    # * ==========================================================
    # * Model
    # * ==========================================================

    @staticmethod
    def is_supported_model(model: str) -> bool:
        return model in SUPPORTED_MODELS

    @staticmethod
    def supported_models():
        return list(SUPPORTED_MODELS)
    

    def _get_client(self):
        """Create the Gemini client lazily."""

        if self._client is not None:
            return self._client

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self._client = genai.Client(
            api_key=self.api_key
        )

        return self._client

    # * ==========================================================
    # * Build conversation
    # * ==========================================================

    def _build_contents(self, session_id: str):
        """
        Convert the standalone chatbot session history into
        Gemini conversation contents.

        Only this chatbot's session is included.
        """

        session = chat_sessions.get_session(session_id)

        if session is None:
            raise ValueError(
                f"Chat session not found: {session_id}"
            )

        contents = []

        for message in session.messages:

            role = (
                "user"
                if message.role == "user"
                else "model"
            )

            contents.append(
                types.Content(
                    role=role,
                    parts=[
                        types.Part.from_text(
                            text=message.content
                        )
                    ],
                )
            )

        return contents

    # * ==========================================================
    # * Generate
    # * ==========================================================

    def generate(
        self,
        session_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Send a message using one standalone chatbot session.
        """

        session = chat_sessions.get_session(session_id)

        if session is None:
            raise ValueError(
                f"Chat session not found: {session_id}"
            )

        # * Save user message first.
        chat_sessions.add_message(
            session_id=session_id,
            role="user",
            content=prompt,
        )

        contents = self._build_contents(session_id)

        client = self._get_client()

        model = session.model or self.model

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=(
                    system_prompt
                    or CHATBOT_SYSTEM_PROMPT
                )
            ),
        )

        text = getattr(
            response,
            "text",
            "",
        ) or ""

        # * Save chatbot response.
        chat_sessions.add_message(
            session_id=session_id,
            role="assistant",
            content=text,
        )

        return text

    # * ==========================================================
    # * Streaming
    # * ==========================================================

    def stream(
        self,
        session_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        stop_event=None,
    ) -> Iterator[ChatStreamChunk]:
        """
        Stream a response using one standalone chatbot session.
        """

        try:
            session = chat_sessions.get_session(session_id)

            if session is None:
                raise ValueError(
                    f"Chat session not found: {session_id}"
                )

            # * Save user message.
            chat_sessions.add_message(
                session_id=session_id,
                role="user",
                content=prompt,
            )

            contents = self._build_contents(session_id)

            client = self._get_client()
            
            model = session.model or self.model

            response_stream = (
                client.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            system_prompt
                            or CHATBOT_SYSTEM_PROMPT
                        )
                    ),
                )
            )

            full_response = []

            for chunk in response_stream:

                if (
                    stop_event is not None
                    and stop_event.is_set()
                ):
                    break

                text = getattr(
                    chunk,
                    "text",
                    "",
                ) or ""

                if text:
                    full_response.append(text)

                    yield ChatStreamChunk(
                        text=text,
                        model=model,
                        done=False,
                    )

            # * Save complete response.
            final_text = "".join(full_response)

            chat_sessions.add_message(
                session_id=session_id,
                role="assistant",
                content=final_text,
            )

            yield ChatStreamChunk(
                text="",
                model=model,
                done=True,
            )

        except Exception as exc:

            yield ChatStreamChunk(
                text="",
                model=(
                    session.model
                    if session is not None
                    else self.model
                ),
                done=True,
                error=str(exc),
            )


# * ==============================================================
# * Default standalone chatbot instance
# * ==============================================================

chatbot = AIChatBot()


def ask_chat(
    session_id: str,
    question: str,
    stop_event=None,
):
    """
    Convenience function for a standalone chatbot request.
    """

    return chatbot.stream(
        session_id=session_id,
        prompt=question,
        stop_event=stop_event,
    )


__all__ = [
    "AIChatBot",
    "ChatStreamChunk",
    "CHATBOT_SYSTEM_PROMPT",
    "DEFAULT_MODEL",
    "chatbot",
    "ask_chat",
]
