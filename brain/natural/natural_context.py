"""
JARVIS PRO
Natural Conversation Intelligence

NCI-2: Natural Context Aggregator

This module creates a read-only unified context snapshot
for Natural Conversation Intelligence.

IMPORTANT:

This module does NOT:

    - execute actions
    - call the planner
    - call an AI model
    - modify dispatcher
    - modify fast router
    - modify memory
    - modify conversation state
    - replace ConversationCoordinator
    - replace ContextBuilder

It only reads context that already exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# * ============================================================
# * Natural Context
# * ============================================================

@dataclass(frozen=True)
class NaturalContext:
    """
    Immutable snapshot of information available to
    Natural Conversation Intelligence.
    """

    # * --------------------------------------------------------
    # * Current user input
    # * --------------------------------------------------------

    user_input: str = ""

    # * --------------------------------------------------------
    # * Existing conversation context
    # * --------------------------------------------------------

    conversation: dict[str, Any] = field(
        default_factory=dict
    )

    # * --------------------------------------------------------
    # * Recent conversation messages
    # * --------------------------------------------------------

    recent_messages: tuple[dict[str, Any], ...] = ()

    # * --------------------------------------------------------
    # * Existing user profile
    # * --------------------------------------------------------

    profile: dict[str, Any] = field(
        default_factory=dict
    )

    # * --------------------------------------------------------
    # * Existing memory information
    # * --------------------------------------------------------

    memories: tuple[Any, ...] = ()

    # * --------------------------------------------------------
    # * Existing planner information
    # * --------------------------------------------------------

    planner: dict[str, Any] = field(
        default_factory=dict
    )

    # * --------------------------------------------------------
    # * Existing project information
    # * --------------------------------------------------------

    project: dict[str, Any] = field(
        default_factory=dict
    )

    # * --------------------------------------------------------
    # * Existing screen information
    # * --------------------------------------------------------

    screen: dict[str, Any] = field(
        default_factory=dict
    )

    # * --------------------------------------------------------
    # * Existing conversation state
    # * --------------------------------------------------------

    conversation_state: dict[str, Any] = field(
        default_factory=dict
    )

    # * --------------------------------------------------------
    # * Metadata
    # * --------------------------------------------------------

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# * ============================================================
# * Natural Context Aggregator
# * ============================================================

class NaturalContextAggregator:
    """
    Collects existing JARVIS context into one read-only object.

    The aggregator does NOT become the owner of any context.

    Existing systems remain authoritative.
    """

    # * ========================================================
    # * Build
    # * ========================================================

    def build(
        self,
        *,
        user_input: str = "",
        conversation_context=None,
        conversation_manager=None,
        profile_manager=None,
        state_manager=None,
        ai_context=None,
    ) -> NaturalContext:

        # * ====================================================
        # * 1. Conversation Context
        # * ====================================================

        conversation = self._extract_conversation(
            conversation_context
        )

        # * ====================================================
        # * 2. Recent Messages
        # * ====================================================

        recent_messages = self._extract_recent_messages(
            conversation_manager
        )

        # * ====================================================
        # * 3. Profile
        # * ====================================================

        profile = self._extract_profile(
            profile_manager
        )

        # * ====================================================
        # * 4. Conversation State
        # * ====================================================

        conversation_state = self._extract_state(
            state_manager
        )

        # * ====================================================
        # * 5. Existing AI Context
        # * ====================================================

        memories = ()
        planner = {}
        project = {}
        screen = {}

        if ai_context is not None:

            memories = self._extract_value(
                ai_context,
                "memories",
                default=[],
            )

            planner = self._extract_dict(
                ai_context,
                "planner",
            )

            project = self._extract_dict(
                ai_context,
                "project",
            )

            screen = self._extract_dict(
                ai_context,
                "screen",
            )

            # * Existing AI context may already contain
            # * the latest user input.

            ai_user_input = self._extract_value(
                ai_context,
                "user_input",
                default="",
            )

            if ai_user_input:
                user_input = str(
                    ai_user_input
                )

        # * ====================================================
        # * 6. Metadata
        # * ====================================================

        metadata = {
            "builder": (
                "NaturalContextAggregator"
            ),
            "version": "1.0",
            "recent_message_count": (
                len(recent_messages)
            ),
            "has_conversation": (
                bool(conversation)
            ),
            "has_profile": (
                bool(profile)
            ),
            "has_memories": (
                bool(memories)
            ),
            "has_planner": (
                bool(planner)
            ),
            "has_project": (
                bool(project)
            ),
            "has_screen": (
                bool(screen)
            ),
            "has_conversation_state": (
                bool(conversation_state)
            ),
        }

        # * ====================================================
        # * 7. Return immutable context
        # * ====================================================

        return NaturalContext(

            user_input=(
                user_input or ""
            ),

            conversation=conversation,

            recent_messages=(
                tuple(recent_messages)
            ),

            profile=profile,

            memories=(
                tuple(memories)
            ),

            planner=planner,

            project=project,

            screen=screen,

            conversation_state=(
                conversation_state
            ),

            metadata=metadata,
        )

    # * ========================================================
    # * Conversation Extraction
    # * ========================================================

    @staticmethod
    def _extract_conversation(
        conversation_context,
    ) -> dict[str, Any]:

        if conversation_context is None:
            return {}

        try:

            # * Your ConversationContextManager already
            # * exposes snapshot() in the existing system.

            if hasattr(
                conversation_context,
                "snapshot",
            ):

                snapshot = (
                    conversation_context.snapshot()
                )

                if isinstance(
                    snapshot,
                    dict,
                ):

                    return dict(snapshot)

        except Exception as e:

            print(
                "[NCI-2] "
                f"Conversation context read failed: {e}"
            )

        return {}

    # * ========================================================
    # * Recent Messages
    # * ========================================================

    @staticmethod
    def _extract_recent_messages(
        conversation_manager,
    ) -> list[dict[str, Any]]:

        if conversation_manager is None:
            return []

        try:

            getter = getattr(
                conversation_manager,
                "get_recent_messages",
                None,
            )

            if getter is None:
                return []

            messages = getter(
                limit=10
            )

            result = []

            for message in messages:

                # * ------------------------------------------------
                # * Dataclass / object message
                # * ------------------------------------------------

                if hasattr(
                    message,
                    "__dict__",
                ):

                    result.append(
                        dict(
                            message.__dict__
                        )
                    )

                    continue

                # * ------------------------------------------------
                # * Dictionary message
                # * ------------------------------------------------

                if isinstance(
                    message,
                    dict,
                ):

                    result.append(
                        dict(message)
                    )

            return result

        except Exception as e:

            print(
                "[NCI-2] "
                f"Recent message read failed: {e}"
            )

            return []

    # * ========================================================
    # * Profile
    # * ========================================================

    @staticmethod
    def _extract_profile(
        profile_manager,
    ) -> dict[str, Any]:

        if profile_manager is None:
            return {}

        try:

            # * Preferred API if available.

            if hasattr(
                profile_manager,
                "as_dict",
            ):

                profile = (
                    profile_manager.as_dict()
                )

                if isinstance(
                    profile,
                    dict,
                ):

                    return dict(profile)

            # * Some profile managers expose
            # * a profile attribute.

            profile = getattr(
                profile_manager,
                "profile",
                None,
            )

            if isinstance(
                profile,
                dict,
            ):

                return dict(profile)

        except Exception as e:

            print(
                "[NCI-2] "
                f"Profile read failed: {e}"
            )

        return {}

    # * ========================================================
    # * Conversation State
    # * ========================================================

    @staticmethod
    def _extract_state(
        state_manager,
    ) -> dict[str, Any]:

        if state_manager is None:
            return {}

        try:

            if hasattr(
                state_manager,
                "info",
            ):

                state = (
                    state_manager.info()
                )

                if isinstance(
                    state,
                    dict,
                ):

                    return dict(state)

            if hasattr(
                state_manager,
                "snapshot",
            ):

                state = (
                    state_manager.snapshot()
                )

                if isinstance(
                    state,
                    dict,
                ):

                    return dict(state)

        except Exception as e:

            print(
                "[NCI-2] "
                f"Conversation state read failed: {e}"
            )

        return {}

    # * ========================================================
    # * Generic Value
    # * ========================================================

    @staticmethod
    def _extract_value(
        source,
        name: str,
        default=None,
    ):

        try:

            value = getattr(
                source,
                name,
                default,
            )

            if value is None:
                return default

            return value

        except Exception:

            return default

    # * ========================================================
    # * Generic Dictionary
    # * ========================================================

    @staticmethod
    def _extract_dict(
        source,
        name: str,
    ) -> dict[str, Any]:

        value = (
            NaturalContextAggregator
            ._extract_value(
                source,
                name,
                {},
            )
        )

        if isinstance(
            value,
            dict,
        ):

            return dict(value)

        return {}


# * ============================================================
# * Shared Aggregator
# * ============================================================

natural_context_aggregator = (
    NaturalContextAggregator()
)