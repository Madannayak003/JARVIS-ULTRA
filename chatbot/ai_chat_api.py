"""
JARVIS PRO
Standalone AI Chatbot API

HTTP/API boundary for the independent chatbot.

This module does NOT use:

- JARVIS dispatcher
- Brain
- JARVIS conversation manager
- JARVIS memory
- Agent
"""

from chatbot.ai_chat_bot import (
    DEFAULT_MODEL,
    SUPPORTED_MODELS,
    chatbot,
)
from chatbot.ai_chat_session import chat_sessions


# * ==========================================================
# * Serialization
# * ==========================================================

def _session_to_dict(session):
    """Convert a chatbot session into JSON-safe data."""

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "provider": session.provider,
        "model": session.model,
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp,
            }
            for message in session.messages
        ],
    }


# * ==========================================================
# * Session API
# * ==========================================================

def create_chat():
    """Create a new independent chatbot session."""

    session = chat_sessions.create_session(
        provider="gemini",
        model=chatbot.model or DEFAULT_MODEL,
    )

    chat = _session_to_dict(session)

    return {
        "success": True,
        "chat": chat,
    }


def list_chats():
    """Return all independent chatbot sessions."""

    sessions = chat_sessions.list_sessions()

    chats = [
        _session_to_dict(session)
        for session in sessions
    ]

    return {
        "success": True,

        # * Frontend-friendly name.
        "chats": chats,

        # * Backward-compatible API name.
        "sessions": chats,
    }


def get_chat(session_id: str):
    """Return one independent chatbot session."""

    session = chat_sessions.get_session(
        session_id
    )

    if session is None:
        return {
            "success": False,
            "error": "Chat session not found.",
        }

    chat = _session_to_dict(session)

    return {
        "success": True,

        # * Frontend-friendly name.
        "chat": chat,

        # * Backward-compatible name.
        "session": chat,
    }


def delete_chat(session_id: str):
    """Delete one independent chatbot session."""

    deleted = chat_sessions.delete_session(
        session_id
    )

    if not deleted:
        return {
            "success": False,
            "error": "Chat session not found.",
        }

    return {
        "success": True,
        "session_id": session_id,
    }


def rename_chat(
    session_id: str,
    title: str,
) -> dict:
    """Rename an AI chat session."""

    title = str(title).strip()

    if not title:
        return {
            "success": False,
            "error": "Chat name cannot be empty.",
        }

    if len(title) > 60:
        title = title[:60]

    success = chat_sessions.rename_session(
        session_id=session_id,
        title=title,
    )

    if not success:
        return {
            "success": False,
            "error": "Chat session not found.",
        }

    session = chat_sessions.get_session(session_id)

    return {
        "success": True,
        "session_id": session_id,
        "title": session.title if session else title,
    }

# * ==========================================================
# * Message API
# * ==========================================================

def send_message(
    session_id: str,
    message: str,
    stop_event=None,
):
    """
    Send a message to one chatbot session.

    Returns the complete response.
    """

    message = str(
        message or ""
    ).strip()

    if not message:
        return {
            "success": False,
            "error": "Message cannot be empty.",
        }

    session = chat_sessions.get_session(
        session_id
    )

    if session is None:
        return {
            "success": False,
            "error": "Chat session not found.",
        }

    model = session.model or DEFAULT_MODEL

    try:

        response = chatbot.generate(
            session_id=session_id,
            prompt=message,
        )

        return {
            "success": True,
            "session_id": session_id,
            "response": response,
            "model": model,
        }

    except Exception as exc:

        error_text = str(exc)

        # * --------------------------------------------------
        # * Gemini quota / rate-limit handling
        # * --------------------------------------------------

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
            or "quota" in error_text.lower()
        ):
            return {
                "success": False,
                "session_id": session_id,
                "model": model,
                "error_code": "MODEL_QUOTA_EXCEEDED",
                "error": (
                    f"The selected model '{model}' "
                    "has reached its current Gemini API "
                    "quota or rate limit. "
                    "Please select another model and try again."
                ),
                "raw_error": error_text,
            }

        return {
            "success": False,
            "session_id": session_id,
            "model": model,
            "error": error_text,
        }


# * ==========================================================
# * Streaming API
# * ==========================================================

def stream_message(
    session_id: str,
    message: str,
    stop_event=None,
):
    """
    Stream a chatbot response.

    Yields ChatStreamChunk objects.
    """

    message = str(
        message or ""
    ).strip()

    if not message:
        raise ValueError(
            "Message cannot be empty."
        )

    session = chat_sessions.get_session(
        session_id
    )

    if session is None:
        raise ValueError(
            f"Chat session not found: {session_id}"
        )

    return chatbot.stream(
        session_id=session_id,
        prompt=message,
        stop_event=stop_event,
    )


# * ==========================================================
# * Model API
# * ==========================================================

def get_model():
    """Return the configured chatbot model."""

    return {
        "success": True,
        "provider": "gemini",
        "model": chatbot.model,
        "default_model": DEFAULT_MODEL,
        "models": [
            {
                "id": model,
                "name": model.replace(
                    "gemini-",
                    "Gemini "
                ),
            }
            for model in SUPPORTED_MODELS
        ],
    }


def set_model(
    session_id: str,
    model: str,
):
    """
    Change the model associated with a chatbot session.
    """

    model = str(
        model or ""
    ).strip()

    if not model:
        return {
            "success": False,
            "error": "Model cannot be empty.",
        }

    if not chatbot.is_supported_model(model):
        return {
            "success": False,
            "error": (
                f"Unsupported Gemini model: {model}"
            ),
            "available_models": (
                chatbot.supported_models()
            ),
        }

    session = chat_sessions.get_session(
        session_id
    )

    if session is None:
        return {
            "success": False,
            "error": "Chat session not found.",
        }

    chat_sessions.set_model(
        session_id=session_id,
        provider="gemini",
        model=model,
    )

    return {
        "success": True,
        "session_id": session_id,
        "model": model,
    }


# * ==========================================================
# * Public API
# * ==========================================================

__all__ = [
    "create_chat",
    "list_chats",
    "get_chat",
    "delete_chat",
    "send_message",
    "stream_message",
    "get_model",
    "set_model",
]