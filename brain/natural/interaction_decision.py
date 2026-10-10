"""
JARVIS PRO
Natural Conversation Intelligence
NCI-1: Interaction Decision
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from brain.natural.interaction_mode import (
    InteractionMode,
)


@dataclass(frozen=True)
class InteractionDecision:
    """
    Read-only result produced by Natural Conversation Intelligence.

    This object describes what JARVIS believes the interaction is.

    It does NOT execute anything.
    """

    mode: InteractionMode

    raw_input: str = ""

    intent: Optional[str] = None

    confidence: float = 0.0

    requires_action: bool = False

    reason: str = ""

    def __post_init__(self) -> None:

        confidence = max(
            0.0,
            min(
                1.0,
                float(
                    self.confidence
                ),
            ),
        )

        object.__setattr__(
            self,
            "confidence",
            confidence,
        )

    @property
    def is_conversation(self) -> bool:

        return (
            self.mode
            is InteractionMode.CONVERSATION
        )

    @property
    def is_action(self) -> bool:

        return (
            self.mode
            is InteractionMode.ACTION
        )

    @property
    def is_hybrid(self) -> bool:

        return (
            self.mode
            is InteractionMode.HYBRID
        )

    @property
    def needs_clarification(self) -> bool:

        return (
            self.mode
            is InteractionMode.CLARIFICATION
        )