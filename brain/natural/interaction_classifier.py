"""
JARVIS PRO
Natural Conversation Intelligence

NCI-3: Interaction Classifier

Converts NaturalContext into an InteractionDecision.

IMPORTANT:

This classifier:

    - does NOT execute actions
    - does NOT call dispatcher
    - does NOT call Fast Router
    - does NOT call planner
    - does NOT call an AI model
    - does NOT modify memory
    - does NOT modify conversation state

It only classifies the interaction.
"""

from __future__ import annotations

import re

from brain.natural.interaction_mode import (
    InteractionMode,
)

from brain.natural.interaction_decision import (
    InteractionDecision,
)

from brain.natural.natural_context import (
    NaturalContext,
)


class InteractionClassifier:
    """
    Deterministic first-stage classifier.

    NCI-3 deliberately starts conservative.

    Existing Fast Router and dispatcher remain
    authoritative for actual execution.
    """

    # * ========================================================
    # * Conversation patterns
    # * ========================================================

    CONVERSATION_PATTERNS = (

        r"^what is\b",

        r"^what are\b",

        r"^what's\b",

        r"^who is\b",

        r"^who are\b",

        r"^why\b",

        r"^how does\b",

        r"^how do\b",

        r"^how can\b",

        r"^tell me about\b",

        r"^tell me something\b",

        r"^explain\b",

        r"^describe\b",

        r"^can you explain\b",

        r"^do you think\b",

        r"^what do you think\b",

        r"^how are you\b",

        r"^are you\b",

        r"^do you remember\b",

        r"^what did we\b",

        r"^what were we\b",

        r"^where were we\b",

    )

    # * ========================================================
    # * Explicit action patterns
    # * ========================================================

    ACTION_PATTERNS = (

        r"^open\b",

        r"^close\b",

        r"^launch\b",

        r"^start\b",

        r"^stop\b",

        r"^play\b",

        r"^pause\b",

        r"^resume\b",

        r"^continue\b",

        r"^skip\b",

        r"^next\b",

        r"^previous\b",

        r"^search\b",

        r"^find\b",

        r"^send\b",

        r"^call\b",

        r"^message\b",

        r"^increase\b",

        r"^decrease\b",

        r"^turn\b",

        r"^make\b",

        r"^set\b",

        r"^enable\b",

        r"^disable\b",

        r"^create\b",

        r"^delete\b",

        r"^rename\b",

        r"^move\b",

        r"^copy\b",

        r"^run\b",

        r"^execute\b",

        r"^lock\b",

        r"^shutdown\b",

        r"^restart\b",

    )

    # * ========================================================
    # * Hybrid indicators
    # * ========================================================

    HYBRID_PATTERNS = (

        r"\band tell me\b",

        r"\band explain\b",

        r"\band let me know\b",

        r"\band what do you think\b",

        r"\bthen tell me\b",

        r"\bthen explain\b",

    )

    # * ========================================================
    # * Clarification patterns
    # * ========================================================

    CLARIFICATION_PATTERNS = (

        r"^which one\b",

        r"^which\b",

        r"^what do you mean\b",

        r"^what one\b",

        r"^which app\b",

        r"^which file\b",

        r"^which song\b",

        r"^which video\b",

    )

    # * ========================================================
    # * Main classification
    # * ========================================================

    def classify(
        self,
        context: NaturalContext,
    ) -> InteractionDecision:

        command = (
            context.user_input
            or ""
        ).strip().lower()

        # * ----------------------------------------------------
        # * Empty input
        # * ----------------------------------------------------

        if not command:

            return InteractionDecision(

                mode=(
                    InteractionMode.CLARIFICATION
                ),

                raw_input=command,

                confidence=0.99,

                requires_action=False,

                reason=(
                    "No user input available."
                ),
            )
            
        # * ----------------------------------------------------
        # * Existing Conversation Relation
        # * ----------------------------------------------------
        # * Preserve semantic relations already detected by
        # * ConversationUnderstandingEngine.
        # * ----------------------------------------------------

        relation = str(
            context.conversation.get(
                "relation",
                "",
            )
        ).lower().strip()

        if relation == "correction":

            return InteractionDecision(

                mode=(
                    InteractionMode.ACTION
                ),

                raw_input=command,

                intent="correction",

                confidence=0.95,

                requires_action=True,

                reason=(
                    "Input was identified as "
                    "a correction to the previous interaction."
                ),
            )

        # * ----------------------------------------------------
        # ! Hybrid must be checked before action.
        # * ----------------------------------------------------

        if self._matches_any(
            command,
            self.HYBRID_PATTERNS,
        ):

            return InteractionDecision(

                mode=(
                    InteractionMode.HYBRID
                ),

                raw_input=command,

                intent="hybrid_request",

                confidence=0.91,

                requires_action=True,

                reason=(
                    "Input contains both "
                    "an action and a conversational request."
                ),
            )

        # * ----------------------------------------------------
        # * Explicit clarification
        # * ----------------------------------------------------

        if self._matches_any(
            command,
            self.CLARIFICATION_PATTERNS,
        ):

            return InteractionDecision(

                mode=(
                    InteractionMode.CLARIFICATION
                ),

                raw_input=command,

                intent="clarification",

                confidence=0.90,

                requires_action=False,

                reason=(
                    "Input appears to request "
                    "clarification."
                ),
            )

        # * ----------------------------------------------------
        # * Explicit conversation
        # * ----------------------------------------------------

        if self._matches_any(
            command,
            self.CONVERSATION_PATTERNS,
        ):

            return InteractionDecision(

                mode=(
                    InteractionMode.CONVERSATION
                ),

                raw_input=command,

                intent="conversation",

                confidence=0.94,

                requires_action=False,

                reason=(
                    "Input matches a natural "
                    "conversation pattern."
                ),
            )

        # ! Contextual conversational requests must be recognized before the
        # * generic action-prefix check. Otherwise short prompts such as
        # * "continue" or "show me another" can fall into the planner and ask
        # * for information that the immediately previous answer already made
        # * clear.
        if self._looks_like_contextual_conversation(
            command,
            context,
        ):

            return InteractionDecision(

                mode=(
                    InteractionMode.CONVERSATION
                ),

                raw_input=command,

                intent="contextual_conversation",

                confidence=0.92,

                requires_action=False,

                reason=(
                    "Input appears conversational within "
                    "the active context."
                ),
            )

        # * ----------------------------------------------------
        # * Explicit action
        # * ----------------------------------------------------

        if self._matches_any(
            command,
            self.ACTION_PATTERNS,
        ):

            return InteractionDecision(

                mode=(
                    InteractionMode.ACTION
                ),

                raw_input=command,

                intent="action",

                confidence=0.94,

                requires_action=True,

                reason=(
                    "Input matches an explicit "
                    "action pattern."
                ),
            )

        # * ----------------------------------------------------
        # * Context-dependent action
        # * ----------------------------------------------------

        # * ----------------------------------------------------
        # * Contextual conversation
        #
        # ! IMPORTANT:
        # * Check conversation BEFORE contextual action.
        #
        # * Example:
        #
        # * "tell me more about it"
        #
        # * contains "it", but it is clearly conversational.
        # * ----------------------------------------------------

        if self._looks_like_contextual_conversation(
            command,
            context,
        ):

            return InteractionDecision(

                mode=(
                    InteractionMode.CONVERSATION
                ),

                raw_input=command,

                intent="contextual_conversation",

                confidence=0.92,

                requires_action=False,

                reason=(
                    "Input appears conversational "
                    "within the active context."
                ),
            )

        # * ----------------------------------------------------
        # * Context-dependent action
        #
        # * Only reached if the input was NOT recognized
        # * as contextual conversation.
        # * ----------------------------------------------------

        if self._looks_like_contextual_action(
            command,
            context,
        ):

            return InteractionDecision(

                mode=(
                    InteractionMode.ACTION
                ),

                raw_input=command,

                intent="contextual_action",

                confidence=0.86,

                requires_action=True,

                reason=(
                    "Input appears to be a contextual "
                    "action using the active context."
                ),
            )
        # * ----------------------------------------------------
        # * Contextual conversation
        # * ----------------------------------------------------

        if self._looks_like_contextual_conversation(
            command,
            context,
        ):

            return InteractionDecision(

                mode=(
                    InteractionMode.CONVERSATION
                ),

                raw_input=command,

                intent="contextual_conversation",

                confidence=0.82,

                requires_action=False,

                reason=(
                    "Input appears conversational "
                    "within the active context."
                ),
            )

        # * ----------------------------------------------------
        # * Unknown / ambiguous
        # * ----------------------------------------------------

        return InteractionDecision(

            mode=(
                InteractionMode.CLARIFICATION
            ),

            raw_input=command,

            intent="unknown",

            confidence=0.55,

            requires_action=False,

            reason=(
                "No strong conversation or action "
                "pattern was detected."
            ),
        )

    # * ========================================================
    # * Pattern matching
    # * ========================================================

    @staticmethod
    def _matches_any(
        text: str,
        patterns,
    ) -> bool:

        for pattern in patterns:

            if re.search(
                pattern,
                text,
            ):

                return True

        return False

    # * ========================================================
    # * Contextual Action
    # * ========================================================

    @staticmethod
    def _looks_like_contextual_action(
        command: str,
        context: NaturalContext,
    ) -> bool:

        conversation = (
            context.conversation
        )

        application = str(
            conversation.get(
                "application",
                "",
            )
        ).lower()

        skill = str(
            conversation.get(
                "skill",
                "",
            )
        ).lower()

        # * ----------------------------------------------------
        # * Known short follow-ups
        # * ----------------------------------------------------

        contextual_actions = (

            "make it louder",

            "make it quieter",

            "turn it up",

            "turn it down",

            "pause it",

            "resume it",

            "continue it",

            "skip it",

            "next",

            "previous",

            "close it",

        )

        if command in contextual_actions:

            return bool(
                application
                or skill
            )

        # * ----------------------------------------------------
        # * Context-dependent references
        # * ----------------------------------------------------

        references = (

            " it ",

            " that ",

            " this ",

            " its ",

        )

        padded = (
            f" {command} "
        )

        if any(
            ref in padded
            for ref in references
        ):

            return bool(
                application
                or skill
            )

        return False

    # * ========================================================
    # * Contextual Conversation
    # * ========================================================

    @staticmethod
    def _looks_like_contextual_conversation(
        command: str,
        context: NaturalContext,
    ) -> bool:

        conversation = (
            context.conversation
        )

        active_topic = str(
            conversation.get(
                "topic",
                "",
            )
        ).strip()

        active_task = str(
            conversation.get(
                "task",
                "",
            )
        ).strip()

        active_application = conversation.get("application")
        active_skill = conversation.get("skill")

        # * A completed conversational answer is useful context even when the
        # * deterministic action context has no topic label. The dispatcher
        # * records the current user input before classification, so
        # * ``last_user_input`` alone is not evidence of a previous exchange.
        # * Require the completed assistant turn to avoid guessing for an
        # * isolated prompt such as "Give me an example."
        has_recent_exchange = bool(
            conversation.get("last_assistant_response")
        )

        # * Direct dispatcher callers may not have populated the semantic
        # * response field yet, while the conversation manager already contains
        # * the completed turn. Only accept a prior user/assistant pair from
        # * recent history so an isolated prompt is still not guessed.
        if not has_recent_exchange:
            recent_messages = context.recent_messages or ()
            roles = {
                str(
                    message.get("role", "")
                    if isinstance(message, dict)
                    else getattr(message, "role", "")
                ).lower()
                for message in recent_messages
            }
            has_recent_exchange = {
                "user",
                "assistant",
            }.issubset(roles)

        # * ----------------------------------------------------
        # * Questions using the current context
        # * ----------------------------------------------------

        question_words = (

            "what",

            "why",

            "how",

            "who",

            "where",

        )

        starts_with_question = any(
            command.startswith(
                word + " "
            )
            or command == word
            for word in question_words
        )

        follow_up_command = command.rstrip(".,!?").strip()
        conversational_follow_up = (
            follow_up_command.startswith((
                "give me an example",
                "give an example",
                "show me an example",
                "tell me more",
                "what about ",
                "how about ",
                "can you give me ",
                "can you show me ",
                "can you show ",
                "can you give ",
            ))
            or bool(re.fullmatch(
                r"(?:give|show)(?: me)? (?:another(?: one| example)?|one(?: more| example)?|one simple example)",
                follow_up_command,
            ))
            or follow_up_command in {
                "another example",
                "one more",
            }
        )

        ambiguous_exchange = (
            InteractionClassifier._has_multiple_recent_subjects(context)
        )

        if (
            (starts_with_question or conversational_follow_up)
            and (
                active_topic
                or active_task
                or has_recent_exchange
            )
            and not (
                ambiguous_exchange
                and (
                    conversational_follow_up
                    or bool(re.search(
                        r"\b(?:it|that|this|one)\b",
                        command,
                    ))
                )
            )
            and not (
                conversational_follow_up
                and (active_application or active_skill)
            )
        ):

            return True

        # * ----------------------------------------------------
        # * References to current topic
        # * ----------------------------------------------------

        if (
            active_topic
            and any(
                word in command
                for word in (
                    "about it",
                    "about that",
                    "more about",
                    "tell me more",
                )
            )
        ):

            return True

        # ! Short references that do not name the subject should still remain
        # * conversational when a completed answer is immediately available.
        # ! Do not steal concrete application follow-ups from the existing
        # * action bridge when an application/skill is active.
        conversational_follow_ups = (
            "explain more",
            "explain again",
            "go deeper",
            "tell me more",
            "simplify it",
            "continue",
        )

        if (
            has_recent_exchange
            and (
                conversational_follow_up
                or command.startswith(conversational_follow_ups)
            )
            and not conversation.get("application")
            and not conversation.get("skill")
            and not ambiguous_exchange
        ):

            return True

        return False

    @staticmethod
    def _has_multiple_recent_subjects(
        context: NaturalContext,
    ) -> bool:
        """Keep bare follow-ups conservative after multi-subject turns."""

        conversation = context.conversation or {}
        previous_input = str(
            conversation.get("last_user_input") or ""
        ).strip().lower()

        if previous_input == str(context.user_input or "").strip().lower():
            previous_input = ""

        if not previous_input:
            for message in reversed(context.recent_messages or ()):
                if isinstance(message, dict):
                    role = str(message.get("role", "")).lower()
                    content = str(message.get("content", "")).strip()
                else:
                    role = str(getattr(message, "role", "")).lower()
                    content = str(getattr(message, "content", "")).strip()

                if role == "user" and content:
                    previous_input = content.lower()
                    break

        return bool(
            previous_input
            and re.search(r"\b(?:and|or)\b", previous_input)
        )


# * ============================================================
# * Shared Classifier
# * ============================================================

interaction_classifier = (
    InteractionClassifier()
)
