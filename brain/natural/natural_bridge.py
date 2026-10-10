"""
JARVIS PRO
Natural Conversation Intelligence

NCI-8: Natural Context Bridge

Connects existing JARVIS context to the NCI pipeline.

This bridge:
    - reads existing JARVIS state
    - builds NaturalContext
    - runs NCI
    - returns ConversationRequest

It does NOT:
    - execute actions
    - call Fast Router
    - call Dispatcher
    - call Ollama
    - modify memory
    - modify conversation state
"""

from __future__ import annotations

from .natural_context import (
    natural_context_aggregator,
)

from .natural_pipeline import (
    natural_conversation_pipeline,
)


class NaturalConversationBridge:

    def process(
        self,
        *,
        user_input: str,
        conversation_context=None,
        conversation_manager=None,
        profile_manager=None,
        state_manager=None,
        ai_context=None,
    ):
        """
        Build the real NaturalContext from JARVIS
        and run NCI-3 -> NCI-7.
        """

        # * ====================================================
        # * NCI-2
        # * Build unified natural context
        # * ====================================================

        natural_context = (
            natural_context_aggregator.build(

                user_input=user_input,

                conversation_context=(
                    conversation_context
                ),

                conversation_manager=(
                    conversation_manager
                ),

                profile_manager=(
                    profile_manager
                ),

                state_manager=(
                    state_manager
                ),

                ai_context=(
                    ai_context
                ),
            )
        )

        # * ====================================================
        # * NCI-3 -> NCI-7
        # * Run natural conversation pipeline
        # * ====================================================

        request = (
            natural_conversation_pipeline.process(
                context=natural_context
            )
        )

        return request


# * ============================================================
# * Shared Bridge
# * ============================================================

natural_conversation_bridge = (
    NaturalConversationBridge()
)