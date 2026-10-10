"""
JARVIS PRO
Natural Conversation Intelligence

NCI-4: Intent & Meaning Understanding

This module determines what the user is trying to mean
after NCI-3 has classified the interaction.

IMPORTANT:

This module does NOT:

    - execute actions
    - call dispatcher
    - call Fast Router
    - call planner
    - call an AI model
    - modify memory
    - modify conversation context
    - replace FollowUpResolver

It only produces a semantic interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from brain.natural.interaction_decision import (
    InteractionDecision,
)

from brain.natural.interaction_mode import (
    InteractionMode,
)

from brain.natural.natural_context import (
    NaturalContext,
)


# * ============================================================
# * NCI-4 Meaning
# * ============================================================

@dataclass(frozen=True)
class MeaningUnderstanding:
    """
    Semantic interpretation of the user's request.
    """

    raw_input: str = ""

    mode: InteractionMode = (
        InteractionMode.CLARIFICATION
    )

    intent: str = "unknown"

    relation: Optional[str] = None

    topic: Optional[str] = None

    task: Optional[str] = None

    object: Optional[str] = None

    reference: Optional[str] = None

    application: Optional[str] = None

    skill: Optional[str] = None

    confidence: float = 0.0

    reason: str = ""

    metadata: dict = field(
        default_factory=dict
    )


# * ============================================================
# * Meaning Understanding Engine
# * ============================================================

class MeaningUnderstandingEngine:
    """
    Deterministic semantic understanding layer.

    NCI-4 sits after NCI-3.

        NaturalContext
              ↓
        NCI-3 Classifier
              ↓
        NCI-4 Meaning
    """

    # * ========================================================
    # * Main method
    # * ========================================================

    def understand(
        self,
        *,
        context: NaturalContext,
        decision: InteractionDecision,
    ) -> MeaningUnderstanding:

        command = (
            context.user_input
            or ""
        ).strip().lower()

        conversation = (
            context.conversation
        )

        application = self._value(
            conversation,
            "application",
        )

        skill = self._value(
            conversation,
            "skill",
        )

        active_topic = self._value(
            conversation,
            "topic",
        )

        active_task = self._value(
            conversation,
            "task",
        )

        active_object = self._value(
            conversation,
            "object",
        )
        
        # * ====================================================
        # * Clarification
        # * ====================================================

        if (
            decision.mode
            is InteractionMode.CLARIFICATION
        ):

            return self._result(
                context=context,
                decision=decision,
                intent="clarification",
                topic=active_topic,
                task=active_task,
                object=active_object,
                application=application,
                skill=skill,
                confidence=0.94,
                reason=(
                    "Input was classified as a "
                    "clarification request."
                ),
            )

        # * A contextual conversational request is a real follow-up even when
        # * it does not contain an explicit pronoun. Preserve that relationship
        # * for the existing FollowUpResolver so the dispatcher can choose the
        # * chat path before the planner sees the short, context-free wording.
        if decision.intent == "contextual_conversation":

            return self._result(
                context=context,
                decision=decision,
                intent="contextual_conversation",
                relation="follow_up",
                topic=active_topic,
                task=active_task,
                object=active_object,
                reference=self._find_reference(command),
                application=application,
                skill=skill,
                confidence=0.92,
                reason=(
                    "Input continues the completed conversational "
                    "exchange."
                ),
            )

        # * ====================================================
        # * Empty input
        # * ====================================================

        if not command:

            return MeaningUnderstanding(

                raw_input=command,

                mode=decision.mode,

                intent="unknown",

                confidence=0.99,

                reason=(
                    "No input was supplied."
                ),
            )
            
        # * ====================================================
        # * Clarification
        #
        # * NCI-3 has already determined that the user is
        # * asking for clarification.
        #
        # * Preserve that decision instead of allowing the
        # * request to fall through into general conversation.
        # * ====================================================

        if (
            decision.mode
            is InteractionMode.CLARIFICATION
        ):

            return self._result(
                context=context,
                decision=decision,
                intent="clarification",
                topic=active_topic,
                task=active_task,
                object=active_object,
                application=application,
                skill=skill,
                confidence=0.94,
                reason=(
                    "Input was classified as a "
                    "clarification request."
                ),
            )    

        # * ====================================================
        # * Explicit project discussion
        # * ====================================================

        if self._starts_with_any(
            command,
            (
                "what do you think about",
                "what do you think of",
                "tell me about our project",
                "tell me about this project",
                "what is our project",
            ),
        ):

            project = (
                self._project_name(
                    context
                )
            )

            return self._result(
                context=context,
                decision=decision,
                intent="project_discussion",
                topic="project",
                object=project,
                confidence=0.94,
                reason=(
                    "Input asks for discussion "
                    "about the project."
                ),
            )

        # * ====================================================
        # * Continue / previous work
        # * ====================================================

        if self._matches_any(
            command,
            (
                "what were we doing",
                "where were we",
                "what did we do",
                "where did we leave off",
                "continue where we left off",
                "what were we working on",
            ),
        ):

            return self._result(
                context=context,
                decision=decision,
                intent="continue_context",
                topic=(
                    active_topic
                    or "current_project"
                ),
                task=active_task,
                object=(
                    active_object
                    or self._project_name(
                        context
                    )
                ),
                application=application,
                skill=skill,
                confidence=0.95,
                reason=(
                    "Input refers to previous "
                    "work or conversation context."
                ),
            )

        # * ====================================================
        # * Tell me more
        # * ====================================================

        if self._matches_any(
            command,
            (
                "tell me more",
                "tell me more about it",
                "tell me more about that",
                "explain more",
                "explain that",
                "explain it",
                "say more about it",
            ),
        ):

            return self._result(
                context=context,
                decision=decision,
                intent="explain_current_subject",
                topic=active_topic,
                task=active_task,
                object=active_object,
                reference=(
                    "it"
                    if "it" in command
                    else "that"
                ),
                application=application,
                skill=skill,
                confidence=0.93,
                reason=(
                    "Input asks for more information "
                    "about the active subject."
                ),
            )

        # * ====================================================
        # * Current application discussion
        # * ====================================================

        if application:

            if self._matches_any(
                command,
                (
                    "what is playing",
                    "what am i listening to",
                    "what am i watching",
                    "what is this",
                    "what is this about",
                ),
            ):

                return self._result(
                    context=context,
                    decision=decision,
                    intent="current_media_question",
                    topic=active_topic,
                    task=active_task,
                    object=active_object,
                    application=application,
                    skill=skill,
                    confidence=0.91,
                    reason=(
                        "Input asks about the "
                        "currently active application."
                    ),
                )
                
        # * ====================================================
        # * What / why / how about current subject
        # * ====================================================

        if (
            active_topic
            and self._starts_with_any(
                command,
                (
                    "what ",
                    "why ",
                    "how ",
                    "who ",
                    "where ",
                ),
            )
        ):

            return self._result(
                context=context,
                decision=decision,
                intent="contextual_question",
                topic=active_topic,
                task=active_task,
                object=active_object,
                application=application,
                skill=skill,
                confidence=0.88,
                reason=(
                    "Question appears to refer "
                    "to the active conversational context."
                ),
            )

        # * ====================================================
        # * Follow-up reference
        # * ====================================================

        if self._contains_reference(
            command
        ):

            return self._result(
                context=context,
                decision=decision,
                intent="contextual_reference",
                relation="reference",
                topic=active_topic,
                task=active_task,
                object=active_object,
                reference=self._find_reference(
                    command
                ),
                application=application,
                skill=skill,
                confidence=0.84,
                reason=(
                    "Input contains a reference "
                    "to an existing conversational subject."
                ),
            )

        # * ====================================================
        # * Explicit conversation
        # * ====================================================

        if (
            decision.mode
            is InteractionMode.CONVERSATION
        ):

            return self._result(
                context=context,
                decision=decision,
                intent="general_conversation",
                topic=active_topic,
                task=active_task,
                object=active_object,
                application=application,
                skill=skill,
                confidence=0.82,
                reason=(
                    "Input is conversational but "
                    "has no more specific semantic intent."
                ),
            )

        # * ====================================================
        # * Explicit action
        # * ====================================================

        if (
            decision.mode
            is InteractionMode.ACTION
        ):

            return self._result(
                context=context,
                decision=decision,
                intent=(
                    decision.intent
                    or "action"
                ),
                topic=active_topic,
                task=active_task,
                object=active_object,
                application=application,
                skill=skill,
                confidence=0.80,
                reason=(
                    "Action meaning is preserved "
                    "for the existing execution layer."
                ),
            )

        # * ====================================================
        # * Hybrid
        # * ====================================================

        if (
            decision.mode
            is InteractionMode.HYBRID
        ):

            return self._result(
                context=context,
                decision=decision,
                intent="hybrid_request",
                topic=active_topic,
                task=active_task,
                object=active_object,
                application=application,
                skill=skill,
                confidence=0.86,
                reason=(
                    "Input contains both action "
                    "and conversational meaning."
                ),
            )

        # * ====================================================
        # * Unknown
        # * ====================================================

        return self._result(
            context=context,
            decision=decision,
            intent="unknown",
            topic=active_topic,
            task=active_task,
            object=active_object,
            application=application,
            skill=skill,
            confidence=0.55,
            reason=(
                "No specific semantic meaning "
                "could be determined."
            ),
        )

    # * ========================================================
    # * Result helper
    # * ========================================================

    @staticmethod
    def _result(
        *,
        context: NaturalContext,
        decision: InteractionDecision,
        intent: str,
        relation: Optional[str] = None,
        topic: Optional[str] = None,
        task: Optional[str] = None,
        object: Optional[str] = None,
        reference: Optional[str] = None,
        application: Optional[str] = None,
        skill: Optional[str] = None,
        confidence: float = 0.0,
        reason: str = "",
    ) -> MeaningUnderstanding:

        return MeaningUnderstanding(

            raw_input=(
                context.user_input
            ),

            mode=decision.mode,

            intent=intent,
            
            relation=relation,

            topic=topic,

            task=task,

            object=object,

            reference=reference,

            application=application,

            skill=skill,

            confidence=confidence,

            reason=reason,

        )

    # * ========================================================
    # * Helpers
    # * ========================================================

    @staticmethod
    def _value(
        source,
        key: str,
    ) -> Optional[str]:

        value = source.get(
            key
        )

        if value is None:
            return None

        value = str(
            value
        ).strip()

        return (
            value
            if value
            else None
        )

    @staticmethod
    def _starts_with_any(
        text: str,
        phrases,
    ) -> bool:

        return any(
            text.startswith(
                phrase
            )
            for phrase in phrases
        )

    @staticmethod
    def _matches_any(
        text: str,
        phrases,
    ) -> bool:

        return any(
            text == phrase
            for phrase in phrases
        )

    @staticmethod
    def _contains_reference(
        text: str,
    ) -> bool:

        import re

        # * ----------------------------------------------------
        # * Pronoun references
        # * ----------------------------------------------------

        if re.search(
            r"\b(?:it|that|this|they|them|those)\b",
            text,
        ):
            return True

        # * ----------------------------------------------------
        # * Positional references
        #
        # * Accept both:
        #
        # * first one
        # * the first one
        #
        # * second one
        # * the second one
        #
        # * and so on.
        # * ----------------------------------------------------

        positional_patterns = (
            r"\b(?:the\s+)?first one\b",
            r"\b(?:the\s+)?second one\b",
            r"\b(?:the\s+)?third one\b",
            r"\b(?:the\s+)?fourth one\b",
            r"\b(?:the\s+)?fifth one\b",

            r"\bnumber one\b",
            r"\bnumber two\b",
            r"\bnumber three\b",
            r"\bnumber four\b",
            r"\bnumber five\b",

            r"\bthe last one\b",
            r"\b(?:the\s+)?next one\b",
            r"\bthe previous one\b",
            r"\bthe same one\b",
        )

        return any(
            re.search(
                pattern,
                text,
            )
            for pattern in positional_patterns
        )

    @staticmethod
    def _find_reference(
        text: str,
    ) -> Optional[str]:

        import re

        # * ----------------------------------------------------
        # * Positional references
        #
        # * Canonical form is returned so downstream
        # * ReferenceResolver logic can use it consistently.
        # * ----------------------------------------------------

        positional_references = (
            (
                r"\b(?:the\s+)?first one\b",
                "the first one",
            ),

            (
                r"\b(?:the\s+)?second one\b",
                "the second one",
            ),

            (
                r"\b(?:the\s+)?third one\b",
                "the third one",
            ),

            (
                r"\b(?:the\s+)?fourth one\b",
                "the fourth one",
            ),

            (
                r"\b(?:the\s+)?fifth one\b",
                "the fifth one",
            ),

            (
                r"\bnumber one\b",
                "number one",
            ),

            (
                r"\bnumber two\b",
                "number two",
            ),

            (
                r"\bnumber three\b",
                "number three",
            ),

            (
                r"\bnumber four\b",
                "number four",
            ),

            (
                r"\bnumber five\b",
                "number five",
            ),

            (
                r"\bthe last one\b",
                "the last one",
            ),

            (
                r"\b(?:the\s+)?next one\b",
                "the next one",
            ),

            (
                r"\bthe previous one\b",
                "the previous one",
            ),

            (
                r"\bthe same one\b",
                "the same one",
            ),
        )

        for pattern, reference in positional_references:

            if re.search(
                pattern,
                text,
            ):
                return reference

        # * ----------------------------------------------------
        # * Pronoun references
        # * ----------------------------------------------------

        for reference in (
            "it",
            "that",
            "this",
            "they",
            "them",
            "those",
        ):

            if re.search(
                rf"\b{re.escape(reference)}\b",
                text,
            ):
                return reference

        return None

    @staticmethod
    def _project_name(
        context: NaturalContext,
    ) -> Optional[str]:

        project = (
            context.project
        )

        name = project.get(
            "name"
        )

        if name:
            return str(
                name
            )

        profile = (
            context.profile
        )

        name = profile.get(
            "current_project"
        )

        if name:
            return str(
                name
            )

        return None


# * ============================================================
# * Shared Engine
# * ============================================================

meaning_understanding_engine = (
    MeaningUnderstandingEngine()
)
