"""
JARVIS PRO
Phase 11.3.5

Clarification Manager

Provides a unified conversational representation for
pending clarification questions.

IMPORTANT:

This module does NOT replace the existing JARVIS
confirmation or clarification systems.

Existing systems remain authoritative, including:

    core.confirmation
    core.whatsapp_memory
    core.context
    core.busy_manager

This module only tracks conversational clarification
information for the Natural Conversation layer.

It does NOT execute commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any, Optional


# * ============================================================
# * Clarification State
# * ============================================================

@dataclass
class ClarificationState:

    # * --------------------------------------------------------
    # * Whether JARVIS is currently waiting for clarification.
    # * --------------------------------------------------------

    waiting: bool = False

    # * --------------------------------------------------------
    # ! What field/information is required.
    #
    # * Examples:
    #
    # * recipient
    # * message
    # * search_platform
    # * project_name
    # * file_name
    # * etc.
    # * --------------------------------------------------------

    field: Optional[str] = None

    # * --------------------------------------------------------
    # * Question asked by JARVIS.
    # * --------------------------------------------------------

    question: Optional[str] = None

    # * --------------------------------------------------------
    # * Original task that requires clarification.
    # * --------------------------------------------------------

    task: Optional[str] = None

    # * --------------------------------------------------------
    # * Original owner/module.
    # * --------------------------------------------------------

    owner: Optional[str] = None

    # * --------------------------------------------------------
    # * Optional metadata.
    # * --------------------------------------------------------

    metadata: dict[str, Any] = None

    # * --------------------------------------------------------
    # * Creation time.
    # * --------------------------------------------------------

    created_at: float = 0.0

    # * --------------------------------------------------------
    # * Timeout.
    # * --------------------------------------------------------

    timeout: int = 120


# * ============================================================
# * Clarification Manager
# * ============================================================

class ClarificationManager:

    def __init__(
        self,
        timeout: int = 120
    ):

        self.state = ClarificationState(
            metadata={},
            timeout=timeout,
        )

    # * ========================================================
    # * Start Clarification
    # * ========================================================

    def start(
        self,
        field: str,
        question: str,
        task: Optional[str] = None,
        owner: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):

        self.state.waiting = True

        self.state.field = field

        self.state.question = question

        self.state.task = task

        self.state.owner = owner

        self.state.metadata = (
            metadata.copy()
            if metadata
            else {}
        )

        self.state.created_at = time()

    # * ========================================================
    # * Check Waiting
    # * ========================================================

    def is_waiting(self) -> bool:

        if not self.state.waiting:

            return False

        elapsed = (
            time()
            - self.state.created_at
        )

        if elapsed > self.state.timeout:

            self.clear()

            return False

        return True

    # * ========================================================
    # * Get Field
    # * ========================================================

    def field(self) -> Optional[str]:

        if not self.is_waiting():

            return None

        return self.state.field

    # * ========================================================
    # * Get Question
    # * ========================================================

    def question(self) -> Optional[str]:

        if not self.is_waiting():

            return None

        return self.state.question

    # * ========================================================
    # * Get Task
    # * ========================================================

    def task(self) -> Optional[str]:

        if not self.is_waiting():

            return None

        return self.state.task

    # * ========================================================
    # * Get Owner
    # * ========================================================

    def owner(self) -> Optional[str]:

        if not self.is_waiting():

            return None

        return self.state.owner

    # * ========================================================
    # * Get Metadata
    # * ========================================================

    def metadata(self) -> dict:

        if not self.is_waiting():

            return {}

        return dict(
            self.state.metadata or {}
        )

    # * ========================================================
    # * Resolve
    # * ========================================================

    def resolve(
        self,
        value: Any
    ) -> Optional[dict]:

        if not self.is_waiting():

            return None

        result = {

            "field":
                self.state.field,

            "value":
                value,

            "task":
                self.state.task,

            "owner":
                self.state.owner,

            "metadata":
                dict(
                    self.state.metadata or {}
                ),

        }

        self.clear()

        return result

    # * ========================================================
    # * Clear
    # * ========================================================

    def clear(self):

        timeout = self.state.timeout

        self.state = ClarificationState(
            metadata={},
            timeout=timeout,
        )

    # * ========================================================
    # * Info
    # * ========================================================

    def info(self) -> dict:

        return {

            "waiting":
                self.is_waiting(),

            "field":
                self.state.field,

            "question":
                self.state.question,

            "task":
                self.state.task,

            "owner":
                self.state.owner,

            "metadata":
                dict(
                    self.state.metadata or {}
                ),

            "created_at":
                self.state.created_at,

            "timeout":
                self.state.timeout,

        }

    # * ========================================================
    # * Representation
    # * ========================================================

    def __repr__(self):

        return (
            "<ClarificationManager "
            f"waiting={self.state.waiting} "
            f"field={self.state.field!r} "
            f"owner={self.state.owner!r}>"
        )


# * ============================================================
# * Shared Manager
# * ============================================================

clarification_manager = ClarificationManager()


# * ============================================================
# * Convenience Functions
# * ============================================================

def start(
    field: str,
    question: str,
    task: Optional[str] = None,
    owner: Optional[str] = None,
    metadata: Optional[dict] = None,
):

    clarification_manager.start(
        field=field,
        question=question,
        task=task,
        owner=owner,
        metadata=metadata,
    )


def is_waiting() -> bool:

    return clarification_manager.is_waiting()


def resolve(
    value: Any
):

    return clarification_manager.resolve(
        value
    )


def clear():

    clarification_manager.clear()


def info() -> dict:

    return clarification_manager.info()