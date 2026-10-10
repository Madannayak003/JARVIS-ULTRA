"""
JARVIS PRO
Stage 4 - Conversation Manager

Handles short-term conversation memory for the current session.

Author: Madan
"""

from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
import uuid
import json
import os


# * ============================================================
# * Message Model
# * ============================================================

@dataclass
class Message:
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = None


# * ============================================================
# * Conversation Manager
# * ============================================================

class ConversationManager:

    def __init__(self, max_messages: int = 50):

        self.max_messages = max_messages
        self.messages = deque(maxlen=max_messages)

        self.session_id = str(uuid.uuid4())

        self.started_at = datetime.now()

    # * --------------------------------------------------------

    def add_user_message(self, text: str, metadata=None):

        self.messages.append(
            Message(
                role="user",
                content=text,
                timestamp=datetime.now().isoformat(timespec="seconds"),
                metadata=metadata
            )
        )

    # * --------------------------------------------------------

    def add_assistant_message(self, text: str, metadata=None):

        self.messages.append(
            Message(
                role="assistant",
                content=text,
                timestamp=datetime.now().isoformat(timespec="seconds"),
                metadata=metadata
            )
        )

    # * --------------------------------------------------------

    def add_system_message(self, text: str):

        self.messages.append(
            Message(
                role="system",
                content=text,
                timestamp=datetime.now().isoformat(timespec="seconds"),
                metadata=None
            )
        )

    # * --------------------------------------------------------

    def get_recent_messages(self, limit: int = 10) -> List[Message]:

        return list(self.messages)[-limit:]

    # * --------------------------------------------------------

    def get_all_messages(self) -> List[Message]:

        return list(self.messages)

    # * --------------------------------------------------------

    def clear(self):

        self.messages.clear()

    # * --------------------------------------------------------

    def new_session(self):

        self.clear()

        self.session_id = str(uuid.uuid4())

        self.started_at = datetime.now()

    # * --------------------------------------------------------

    def get_session_id(self):

        return self.session_id

    # * --------------------------------------------------------

    def save_json(self, filepath="conversation.json"):

        data = {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "messages": [
                asdict(msg)
                for msg in self.messages
            ]
        }

        with open(filepath, "w", encoding="utf8") as f:
            json.dump(data, f, indent=4)

    # * --------------------------------------------------------

    def load_json(self, filepath="conversation.json"):

        if not os.path.exists(filepath):
            return

        with open(filepath, "r", encoding="utf8") as f:
            data = json.load(f)

        self.session_id = data["session_id"]

        self.messages.clear()

        for item in data["messages"]:

            self.messages.append(
                Message(**item)
            )

    # * --------------------------------------------------------

    def __len__(self):

        return len(self.messages)

    # * --------------------------------------------------------

    def __repr__(self):

        return f"<ConversationManager session={self.session_id[:8]} messages={len(self.messages)}>"