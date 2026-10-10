"""
=============================================================
JARVIS PRO — AI CHAT SESSION MANAGER
=============================================================

Completely independent session/history storage for the
JARVIS PRO AI Chatbot.

IMPORTANT
---------
This module is intentionally isolated from the existing JARVIS
conversation architecture.

It does NOT import or use:

    - brain
    - core.dispatcher
    - JARVIS memory
    - JARVIS conversation manager
    - Agent
    - existing JARVIS context
    - existing JARVIS response pipeline

It only manages AI Chat sessions and their messages.
=============================================================
"""

from __future__ import annotations

import json
import threading
import uuid

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# * =============================================================
# * STORAGE
# * =============================================================

_BASE_DIR = Path(__file__).resolve().parent.parent

_CHAT_DATA_DIR = _BASE_DIR / "data" / "ai_chat"

_CHAT_HISTORY_FILE = _CHAT_DATA_DIR / "chat_history.json"

_LOCK = threading.RLock()


# * =============================================================
# * HELPERS
# * =============================================================

def _utc_now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _ensure_storage() -> None:
    """Create the AI Chat storage directory and file."""
    _CHAT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not _CHAT_HISTORY_FILE.exists():
        _CHAT_HISTORY_FILE.write_text(
            json.dumps(
                {
                    "sessions": []
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


def _load_data() -> Dict[str, Any]:
    """Load the independent AI Chat database."""
    _ensure_storage()

    try:
        data = json.loads(
            _CHAT_HISTORY_FILE.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(data, dict):
            return {"sessions": []}

        if not isinstance(data.get("sessions"), list):
            data["sessions"] = []

        return data

    except (OSError, json.JSONDecodeError):
        return {"sessions": []}


def _save_data(data: Dict[str, Any]) -> None:
    """Save the independent AI Chat database."""
    _ensure_storage()

    temp_file = _CHAT_HISTORY_FILE.with_suffix(".tmp")

    temp_file.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temp_file.replace(_CHAT_HISTORY_FILE)


# * =============================================================
# * MESSAGE
# * =============================================================

@dataclass
class ChatMessage:
    """One message inside an AI Chat session."""

    role: str
    content: str
    timestamp: str = field(
        default_factory=_utc_now
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# * =============================================================
# * CHAT SESSION
# * =============================================================

@dataclass
class ChatSessionRecord:
    """One independent AI Chat conversation."""

    id: str

    title: str = "New Chat"

    created_at: str = field(
        default_factory=_utc_now
    )

    updated_at: str = field(
        default_factory=_utc_now
    )

    messages: List[ChatMessage] = field(
        default_factory=list
    )

    provider: str = "gemini"

    model: str = "gemini-3.6-flash"


# * =============================================================
# * SESSION MANAGER
# * =============================================================

class AIChatSessionManager:
    """
    Independent persistent session manager for AI Chat.

    This class knows nothing about the existing JARVIS
    conversation system.
    """

    def __init__(self) -> None:
        self._lock = _LOCK

    # * ---------------------------------------------------------
    # * CREATE
    # * ---------------------------------------------------------

    def create_session(
        self,
        title: str = "New Chat",
        provider: str = "gemini",
        model: str = "gemini-3.6-flash",
    ) -> ChatSessionRecord:

        session = ChatSessionRecord(
            id=uuid.uuid4().hex,
            title=title.strip() or "New Chat",
            provider=provider,
            model=model,
        )

        with self._lock:
            data = _load_data()

            data["sessions"].append(
                asdict(session)
            )

            _save_data(data)

        return session

    # * ---------------------------------------------------------
    # * GET
    # * ---------------------------------------------------------

    def get_session(
        self,
        session_id: str,
    ) -> Optional[ChatSessionRecord]:

        with self._lock:
            data = _load_data()

            for raw in data["sessions"]:

                if raw.get("id") != session_id:
                    continue

                return self._from_dict(raw)

        return None

    # * ---------------------------------------------------------
    # * LIST
    # * ---------------------------------------------------------

    def list_sessions(self) -> List[ChatSessionRecord]:

        with self._lock:
            data = _load_data()

            sessions = [
                self._from_dict(raw)
                for raw in data["sessions"]
            ]

        sessions.sort(
            key=lambda session: session.updated_at,
            reverse=True,
        )

        return sessions

    # * ---------------------------------------------------------
    # * ADD MESSAGE
    # * ---------------------------------------------------------

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ChatMessage]:

        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )

        with self._lock:
            data = _load_data()

            for raw in data["sessions"]:

                if raw.get("id") != session_id:
                    continue

                raw.setdefault("messages", [])

                raw["messages"].append(
                    asdict(message)
                )

                raw["updated_at"] = _utc_now()

                # * Automatically create a useful title
                # * from the first user message.
                if (
                    role == "user"
                    and raw.get("title") == "New Chat"
                ):
                    title = content.strip()

                    if len(title) > 60:
                        title = title[:57] + "..."

                    raw["title"] = (
                        title or "New Chat"
                    )

                _save_data(data)

                return message

        return None

    # * ---------------------------------------------------------
    # * DELETE
    # * ---------------------------------------------------------

    def delete_session(
        self,
        session_id: str,
    ) -> bool:

        with self._lock:
            data = _load_data()

            original_count = len(
                data["sessions"]
            )

            data["sessions"] = [
                session
                for session in data["sessions"]
                if session.get("id") != session_id
            ]

            if len(data["sessions"]) == original_count:
                return False

            _save_data(data)

            return True
        
    # * ------------------------------------------------------
    # * RENAME
    # * ------------------------------------------------------
        
    def rename_session(
        self,
        session_id: str,
        title: str,
    ) -> bool:
        """Rename an existing chat session."""

        title = str(title).strip()

        if not title:
            return False

        with self._lock:
            data = _load_data()

            for raw in data["sessions"]:
                if raw.get("id") != session_id:
                    continue

                raw["title"] = title[:60]
                raw["updated_at"] = _utc_now()

                _save_data(data)
                return True

        return False

    # * ---------------------------------------------------------
    # * CLEAR ALL
    # * ---------------------------------------------------------

    def clear_all(self) -> None:

        with self._lock:
            _save_data(
                {
                    "sessions": []
                }
            )

    # * ---------------------------------------------------------
    # * UPDATE MODEL
    # * ---------------------------------------------------------

    def set_model(
        self,
        session_id: str,
        provider: str,
        model: str,
    ) -> bool:

        with self._lock:
            data = _load_data()

            for raw in data["sessions"]:

                if raw.get("id") != session_id:
                    continue

                raw["provider"] = provider
                raw["model"] = model
                raw["updated_at"] = _utc_now()

                _save_data(data)

                return True

        return False

    # * ---------------------------------------------------------
    # * INTERNAL CONVERSION
    # * ---------------------------------------------------------

    @staticmethod
    def _from_dict(
        raw: Dict[str, Any],
    ) -> ChatSessionRecord:

        messages = [
            ChatMessage(
                role=message.get(
                    "role",
                    "user",
                ),
                content=message.get(
                    "content",
                    "",
                ),
                timestamp=message.get(
                    "timestamp",
                    _utc_now(),
                ),
                metadata=message.get(
                    "metadata",
                    {},
                ),
            )
            for message in raw.get(
                "messages",
                [],
            )
        ]

        return ChatSessionRecord(
            id=raw.get(
                "id",
                uuid.uuid4().hex,
            ),
            title=raw.get(
                "title",
                "New Chat",
            ),
            created_at=raw.get(
                "created_at",
                _utc_now(),
            ),
            updated_at=raw.get(
                "updated_at",
                _utc_now(),
            ),
            messages=messages,
            provider=raw.get(
                "provider",
                "gemini",
            ),
            model=raw.get(
                "model",
                "gemini-3.6-flash",
            ),
        )


# * =============================================================
# * SINGLE MANAGER INSTANCE
# * =============================================================

chat_sessions = AIChatSessionManager()


__all__ = [
    "ChatMessage",
    "ChatSessionRecord",
    "AIChatSessionManager",
    "chat_sessions",
]