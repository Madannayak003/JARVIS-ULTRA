"""
JARVIS PRO
Phase 11.3.4

Follow-up Resolver

Combines:

    - Conversation Understanding
    - Conversation Context
    - Reference Resolution

to produce a structured conversational request.

IMPORTANT:

This module does NOT execute commands.

It does NOT call:

    - Dispatcher
    - Planner
    - Skills
    - IntentEngine
    - Memory
    - core.assistant

It only resolves conversational meaning.

The existing JARVIS execution architecture remains
unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from brain.conversation_understanding import (
    ConversationRelation,
    ConversationUnderstanding,
)

from brain.reference_resolver import (
    ReferenceResolver,
    ReferenceResolution,
)


# * ============================================================
# * Follow-up Resolution Result
# * ============================================================

@dataclass
class FollowUpResolution:

    # * --------------------------------------------------------
    # * Whether this input should be treated as conversational
    # * continuation/follow-up.
    # * --------------------------------------------------------

    is_follow_up: bool = False

    # * --------------------------------------------------------
    # * Original user input
    # * --------------------------------------------------------

    raw_input: str = ""

    # * --------------------------------------------------------
    # * Conversation relationship
    # * --------------------------------------------------------

    relation: Optional[str] = None

    # * --------------------------------------------------------
    # * Current application
    # * --------------------------------------------------------

    application: Optional[str] = None

    # * --------------------------------------------------------
    # * Current skill
    # * --------------------------------------------------------

    skill: Optional[str] = None

    # * --------------------------------------------------------
    # * Current topic
    # * --------------------------------------------------------

    topic: Optional[str] = None

    # * --------------------------------------------------------
    # * Current task
    # * --------------------------------------------------------

    task: Optional[str] = None

    # * --------------------------------------------------------
    # * Current intent
    # * --------------------------------------------------------

    intent: Optional[str] = None

    # * --------------------------------------------------------
    # * Current action
    # * --------------------------------------------------------

    action: Optional[str] = None

    # * --------------------------------------------------------
    # * Current object
    # * --------------------------------------------------------

    object: Optional[Any] = None

    # * --------------------------------------------------------
    # * Detected references
    # * --------------------------------------------------------

    references: list[str] = field(
        default_factory=list
    )

    # * --------------------------------------------------------
    # * Resolved references
    #
    # * Example:
    #
    # * {
    # * "it": "music"
    # * }
    # * --------------------------------------------------------

    resolved_references: dict[str, Any] = field(
        default_factory=dict
    )

    # * --------------------------------------------------------
    # * Unresolved references
    # * --------------------------------------------------------

    unresolved_references: list[str] = field(
        default_factory=list
    )

    # * --------------------------------------------------------
    # * Confidence
    # * --------------------------------------------------------

    confidence: float = 0.0

    # * --------------------------------------------------------
    # * Explanation
    # * --------------------------------------------------------

    reason: str = ""


# * ============================================================
# * Follow-up Resolver
# * ============================================================

class FollowUpResolver:

    def __init__(
        self,
        reference_resolver: Optional[
            ReferenceResolver
        ] = None,
    ):

        self.reference_resolver = (
            reference_resolver
            or ReferenceResolver()
        )

    # * ========================================================
    # * Public API
    # * ========================================================

    def resolve(
        self,
        understanding: ConversationUnderstanding,
        context=None,
    ) -> FollowUpResolution:

        if understanding is None:

            return FollowUpResolution(
                is_follow_up=False,
                reason=(
                    "No conversation understanding "
                    "was provided."
                ),
            )

        relation = understanding.relation

        raw_input = (
            understanding.raw_input
        )

        references = list(
            understanding.references or []
        )

        # * ----------------------------------------------------
        # * Determine whether this is a follow-up.
        #
        # * Reference-containing requests are also potentially
        # * contextual requests.
        # * ----------------------------------------------------

        is_follow_up = relation in {

            ConversationRelation.FOLLOW_UP,

            ConversationRelation.CONTINUATION,

            ConversationRelation.CORRECTION,

            ConversationRelation.REFERENCE,

        }

        # * ----------------------------------------------------
        # * Extract existing context.
        # * ----------------------------------------------------

        context_values = self._get_context(
            context
        )

        # * ----------------------------------------------------
        # * Resolve references.
        # * ----------------------------------------------------

        resolved_references = {}

        unresolved_references = []

        for reference in references:

            result = (
                self.reference_resolver.resolve(
                    reference,
                    context,
                )
            )

            if result.resolved:

                resolved_references[
                    reference
                ] = result.value

            else:

                unresolved_references.append(
                    reference
                )

        # * ----------------------------------------------------
        # * Determine contextual object.
        # * ----------------------------------------------------

        resolved_object = (
            context_values.get("object")
        )

        # * ----------------------------------------------------
        # * If a reference resolved successfully, use it.
        #
        # ! We intentionally do NOT overwrite the active object
        # * unless the reference itself resolved.
        # * ----------------------------------------------------

        if resolved_references:

            # * Prefer the first resolved reference.
            first_reference = next(
                iter(
                    resolved_references
                )
            )

            resolved_object = (
                resolved_references[
                    first_reference
                ]
            )

        # * ----------------------------------------------------
        # * Determine confidence.
        # * ----------------------------------------------------

        confidence = (
            understanding.confidence
        )

        if references:

            if unresolved_references:

                confidence *= 0.75

            elif resolved_references:

                confidence = min(
                    0.99,
                    confidence + 0.08
                )

        # * ----------------------------------------------------
        # * Build explanation.
        # * ----------------------------------------------------

        reason = self._build_reason(
            relation=relation,
            references=references,
            resolved_references=resolved_references,
            unresolved_references=unresolved_references,
            context_values=(
                context_values
                if is_follow_up
                else {}
            ),
        )

        # * ----------------------------------------------------
        # * Context inheritance
        #
        # * Existing conversational context should only be
        # * inherited when this request is actually a follow-up.
        #
        # ! A NEW_REQUEST must NOT inherit the previous
        # * application's context.
        # * ----------------------------------------------------

        if is_follow_up:

            active_application = (
                context_values.get(
                    "application"
                )
            )

            active_skill = (
                context_values.get(
                    "skill"
                )
            )

            active_topic = (
                context_values.get(
                    "topic"
                )
            )

            active_task = (
                context_values.get(
                    "task"
                )
            )

            active_intent = (
                context_values.get(
                    "intent"
                )
            )

            active_action = (
                context_values.get(
                    "action"
                )
            )

            active_object = resolved_object

        else:

            active_application = None

            active_skill = None

            active_topic = None

            active_task = None

            active_intent = None

            active_action = None

            active_object = None


        return FollowUpResolution(

            is_follow_up=is_follow_up,

            raw_input=raw_input,

            relation=getattr(relation, "value", relation),

            application=active_application,

            skill=active_skill,

            topic=active_topic,

            task=active_task,

            intent=active_intent,

            action=active_action,

            object=active_object,

            references=references,

            resolved_references=(
                resolved_references
            ),

            unresolved_references=(
                unresolved_references
            ),

            confidence=confidence,

            reason=reason,

        )

    # * ========================================================
    # * Context Extraction
    # * ========================================================

    @staticmethod
    def _get_context(
        context
    ) -> dict:

        values = {

            "topic": None,

            "task": None,

            "application": None,

            "skill": None,

            "intent": None,

            "action": None,

            "object": None,

            "objects": None,

            "referenced_object": None,

            "last_result": None,

        }

        if context is None:

            return values

        # * ----------------------------------------------------
        # * ConversationContextManager
        # * ----------------------------------------------------

        if hasattr(
            context,
            "get"
        ):

            for key in values:

                try:

                    values[key] = (
                        context.get(key)
                    )

                except Exception:

                    pass

            return values

        # * ----------------------------------------------------
        # * Dictionary
        # * ----------------------------------------------------

        if isinstance(
            context,
            dict
        ):

            for key in values:

                if key in context:

                    values[key] = (
                        context[key]
                    )

            return values

        # * ----------------------------------------------------
        # * ConversationContext object
        # * ----------------------------------------------------

        for key in values:

            try:

                values[key] = getattr(
                    context,
                    key,
                    None
                )

            except Exception:

                pass

        return values

    # * ========================================================
    # * Explanation
    # * ========================================================

    @staticmethod
    def _build_reason(
        relation,
        references,
        resolved_references,
        unresolved_references,
        context_values,
    ) -> str:

        parts = []

        parts.append(
            f"Conversation relation: "
            f"{getattr(relation, 'value', relation)}"
        )

        if context_values.get(
            "application"
        ):

            parts.append(
                "active application="
                f"{context_values['application']}"
            )

        if context_values.get(
            "skill"
        ):

            parts.append(
                "active skill="
                f"{context_values['skill']}"
            )

        if references:

            parts.append(
                "references="
                f"{references}"
            )

        if resolved_references:

            parts.append(
                "resolved="
                f"{resolved_references}"
            )

        if unresolved_references:

            parts.append(
                "unresolved="
                f"{unresolved_references}"
            )

        return "; ".join(
            parts
        )


# * ============================================================
# * Shared Resolver
# * ============================================================

follow_up_resolver = FollowUpResolver()


# * ============================================================
# * Convenience Function
# * ============================================================

def resolve_follow_up(
    understanding: ConversationUnderstanding,
    context=None,
) -> FollowUpResolution:

    return follow_up_resolver.resolve(
        understanding=understanding,
        context=context,
    )