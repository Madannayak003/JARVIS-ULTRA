"""
JARVIS PRO
Stage 5

Conversation State Manager

Tracks which module currently owns
the active conversation.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import time


@dataclass
class ConversationState:

    owner: str | None = None

    waiting: bool = False

    reason: str = ""

    created_at: float = 0.0

    timeout: int = 120


class ConversationStateManager:

    def __init__(self):

        self.state = ConversationState()

    # * --------------------------------------------

    def start(

        self,

        owner: str,

        reason: str = ""

    ):

        self.state.owner = owner

        self.state.waiting = True

        self.state.reason = reason

        self.state.created_at = time()

    # * --------------------------------------------

    def finish(self):

        self.state.owner = None

        self.state.waiting = False

        self.state.reason = ""

        self.state.created_at = 0

    # * --------------------------------------------

    def is_waiting(self):

        if not self.state.waiting:

            return False

        elapsed = time() - self.state.created_at

        if elapsed > self.state.timeout:

            self.finish()

            return False

        return True

    # * --------------------------------------------

    def owner(self):

        return self.state.owner

    # * --------------------------------------------

    def reason(self):

        return self.state.reason

    # * --------------------------------------------

    def reset(self):

        self.finish()

    # * --------------------------------------------

    def info(self):

        return {

            "owner": self.state.owner,

            "waiting": self.state.waiting,

            "reason": self.state.reason,

            "timeout": self.state.timeout

        }