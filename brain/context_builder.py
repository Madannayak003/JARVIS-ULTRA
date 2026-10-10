"""
JARVIS PRO
Stage 4 - Context Builder

Builds a unified AIContext object by collecting data from
Conversation Manager, Profile Manager, Memory Manager,
Planner and Natural Conversation Intelligence.

Author: Madan
"""

from __future__ import annotations

from datetime import datetime

from .context_types import AIContext

from brain.screen_context import screen_context

from brain.natural.natural_bridge import (
    natural_conversation_bridge,
)


class ContextBuilder:

    def __init__(
        self,
        profile_manager,
        conversation_manager,
        memory_manager=None,
        planner=None,
        conversation_context=None,
        state_manager=None,
    ):
        """
        Parameters
        ----------
        profile_manager
            ProfileManager instance

        conversation_manager
            ConversationManager instance

        memory_manager
            Existing memory system (optional)

        planner
            Planner instance (optional)

        conversation_context
            ConversationContextManager instance (optional)

        state_manager
            ConversationStateManager instance (optional)
        """

        self.profile = profile_manager

        self.conversation = conversation_manager

        self.memory = memory_manager

        self.planner = planner

        self.conversation_context = (
            conversation_context
        )

        self.state_manager = (
            state_manager
        )

    # * --------------------------------------------------------
    # * Build Context
    # * --------------------------------------------------------

    def build(
        self,
        user_input: str,
        memory_limit: int = 5,
        conversation_limit: int = 10
    ) -> AIContext:

        context = AIContext()

        # * ----------------------------------------------------
        # * Current user request
        # * ----------------------------------------------------

        context.user_input = user_input

        # * ----------------------------------------------------
        # * Natural Conversation Intelligence
        # * ----------------------------------------------------

        context.natural = {}

        try:

            natural_request = (
                natural_conversation_bridge.process(

                    user_input=user_input,

                    conversation_context=(
                        self.conversation_context
                    ),

                    conversation_manager=(
                        self.conversation
                    ),

                    profile_manager=(
                        self.profile
                    ),

                    state_manager=(
                        self.state_manager
                    ),

                    ai_context=context,
                )
            )

            context.natural = {

                "user_input":
                    natural_request.user_input,

                "intent":
                    natural_request.intent,

                "mode":
                    natural_request.mode,

                "confidence":
                    natural_request.confidence,

                "topic":
                    natural_request.topic,

                "task":
                    natural_request.task,

                "object":
                    natural_request.object,

                "reference":
                    natural_request.reference,

                "references":
                    list(natural_request.references),

                "resolved_references":
                    dict(natural_request.resolved_references),

                "unresolved_references":
                    list(natural_request.unresolved_references),

                "application":
                    natural_request.application,

                "skill":
                    natural_request.skill,

                "needs_ai":
                    natural_request.needs_ai,

                "needs_action":
                    natural_request.needs_action,

                "needs_clarification":
                    natural_request.needs_clarification,

                "instructions":
                    natural_request.instructions,

                "metadata":
                    natural_request.metadata,
            }

        except Exception as e:

            print(
                f"[ContextBuilder] "
                f"Natural context unavailable: {e}"
            )

            context.natural = {}

        # * ----------------------------------------------------
        # * User profile
        # * ----------------------------------------------------

        context.profile = (
            self.profile.as_dict()
        )

        # * ----------------------------------------------------
        # * Recent conversation
        # * ----------------------------------------------------

        messages = (
            self.conversation.get_recent_messages(
                conversation_limit
            )
        )

        context.conversation = [

            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp
            }

            for m in messages
        ]

        # * ----------------------------------------------------
        # * Long-term memory
        # * ----------------------------------------------------

        context.memories = []

        if self.memory is not None:

            try:

                memories = self.memory.search(
                    user_input,
                    limit=memory_limit
                )

                context.memories = memories

            except Exception:

                context.memories = []

        # * ----------------------------------------------------
        # * Planner state
        # * ----------------------------------------------------

        context.planner = {}

        if self.planner is not None:

            try:

                if hasattr(
                    self.planner,
                    "get_state"
                ):

                    context.planner = (
                        self.planner.get_state()
                    )

            except Exception:

                context.planner = {}

        # * ----------------------------------------------------
        # * Live Screen Context
        # * ----------------------------------------------------

        context.screen = {}

        try:

            if screen_context.has_context():

                screen_data = (
                    screen_context.get_context()
                )

                if screen_data:

                    context.screen = screen_data

        except Exception as e:

            print(
                f"[ContextBuilder] "
                f"Screen context unavailable: {e}"
            )

            context.screen = {}

        # * ----------------------------------------------------
        # * Active project
        # * ----------------------------------------------------

        context.project = {

            "name": context.profile.get(
                "current_project",
                ""
            ),

            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            )
        }

        # * ----------------------------------------------------
        # * Tool information
        # * ----------------------------------------------------

        context.tools = {}

        # * ----------------------------------------------------
        # * Metadata
        # * ----------------------------------------------------

        context.metadata = {

            "builder":
                "ContextBuilder",

            "version":
                "1.0",

            "conversation_messages":
                len(context.conversation),

            "memory_results":
                len(context.memories),

            "generated_at":
                datetime.now().isoformat(
                    timespec="seconds"
                )
        }

        return context
