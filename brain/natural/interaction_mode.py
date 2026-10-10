"""
JARVIS PRO
Natural Conversation Intelligence
NCI-1: Interaction Modes
"""

from __future__ import annotations

from enum import Enum


class InteractionMode(str, Enum):
    """
    High-level type of interaction.

    CONVERSATION:
        User primarily wants a natural answer.

    ACTION:
        User wants JARVIS to perform an operation.

    HYBRID:
        User wants JARVIS to perform an operation
        and provide a conversational response.

    CLARIFICATION:
        JARVIS does not have enough information to
        confidently determine the user's intention.
    """

    CONVERSATION = "conversation"

    ACTION = "action"

    HYBRID = "hybrid"

    CLARIFICATION = "clarification"