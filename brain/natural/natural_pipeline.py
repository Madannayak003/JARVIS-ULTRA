"""
JARVIS PRO
Natural Conversation Intelligence

NCI-7: Natural Conversation Pipeline

Connects NCI-3 → NCI-4 → NCI-5 → NCI-6.

This module only performs natural-language understanding.

It does NOT:
    - execute actions
    - call Fast Router
    - call Dispatcher
    - call Planner
    - call an AI model
    - modify memory
    - replace FollowUpResolver
"""

from __future__ import annotations

from .interaction_classifier import (
    InteractionClassifier,
)

from .meaning_understanding import (
    MeaningUnderstandingEngine,
)

from .response_strategy import (
    ResponseStrategyEngine,
)

from .conversation_request import (
    ConversationRequestBuilder,
)


# * ============================================================
# * Natural Conversation Pipeline
# * ============================================================

class NaturalConversationPipeline:

    def __init__(self):

        self.classifier = (
            InteractionClassifier()
        )

        self.meaning_engine = (
            MeaningUnderstandingEngine()
        )

        self.strategy_engine = (
            ResponseStrategyEngine()
        )

        self.request_builder = (
            ConversationRequestBuilder()
        )

    # * ========================================================
    # * Process
    # * ========================================================

    def process(
        self,
        *,
        context,
    ):
        """
        Run the natural conversation pipeline.

        Input:
            NaturalContext

        Output:
            ConversationRequest
        """

        # * ----------------------------------------------------
        # * NCI-3
        # * ----------------------------------------------------

        decision = (
            self.classifier.classify(
                context
            )
        )

        # * ----------------------------------------------------
        # * NCI-4
        # * ----------------------------------------------------

        meaning = (
            self.meaning_engine.understand(

                context=context,

                decision=decision,

            )
        )

        # * ----------------------------------------------------
        # * NCI-5
        # * ----------------------------------------------------

        strategy = (
            self.strategy_engine.decide(
                meaning
            )
        )

        # * ----------------------------------------------------
        # * NCI-6
        # * ----------------------------------------------------

        request = (
            self.request_builder.build(

                user_input=(
                    context.user_input
                ),

                meaning=meaning,

                strategy=strategy,

                context=context,

            )
        )

        return request


# * ============================================================
# * Shared Pipeline
# * ============================================================

natural_conversation_pipeline = (
    NaturalConversationPipeline()
)