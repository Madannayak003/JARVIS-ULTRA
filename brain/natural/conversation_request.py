"""
JARVIS PRO
Natural Conversation Intelligence

NCI-6: Conversation Request Builder

Purpose
-------
Converts the output of NCI-2, NCI-4 and NCI-5 into a
structured request that the existing JARVIS AI/runtime
can use as a common conversational interface.

IMPORTANT:
    This module does NOT:
        - call Ollama
        - execute actions
        - modify the dispatcher
        - modify Fast Router
        - modify FollowUpResolver

It only prepares the meaning of the request.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# * ============================================================
# * Conversation Request
# * ============================================================

@dataclass(frozen=True)
class ConversationRequest:

    # * --------------------------------------------------------
    # * Original request
    # * --------------------------------------------------------

    user_input: str

    # * --------------------------------------------------------
    # * Conversational relationship
    #
    # * Examples:
    #
    # * new_request
    # * follow_up
    # * continuation
    # * reference
    # * correction
    #
    # * This allows the common interface to preserve
    # * conversational context without executing anything.
    # * --------------------------------------------------------

    relation: Optional[str] = None

    # * --------------------------------------------------------
    # * NCI meaning
    # * --------------------------------------------------------

    intent: str = "unknown"

    mode: str = "conversation"

    confidence: float = 0.0

    # * --------------------------------------------------------
    # * Context
    # * --------------------------------------------------------

    topic: Optional[str] = None

    task: Optional[str] = None

    object: Optional[str] = None

    # * --------------------------------------------------------
    # * Reference
    #
    # * Single primary reference retained for compatibility
    # * with the existing NCI representation.
    # * --------------------------------------------------------

    reference: Optional[str] = None

    # * --------------------------------------------------------
    # * References
    #
    # * Example:
    #
    # * ["it"]
    #
    # * This preserves multiple detected references.
    # * --------------------------------------------------------

    references: List[str] = field(
        default_factory=list
    )

    # * --------------------------------------------------------
    # * Resolved references
    #
    # * Example:
    #
    # * {
    # * "it": "video"
    # * }
    # * --------------------------------------------------------

    resolved_references: Dict[str, Any] = field(
        default_factory=dict
    )

    # * --------------------------------------------------------
    # * Unresolved references
    # * --------------------------------------------------------

    unresolved_references: List[str] = field(
        default_factory=list
    )

    # * --------------------------------------------------------
    # * Application
    # * --------------------------------------------------------

    application: Optional[str] = None

    # * --------------------------------------------------------
    # * Skill
    # * --------------------------------------------------------

    skill: Optional[str] = None

    # * --------------------------------------------------------
    # * Action
    #
    # * This is optional because NCI does not necessarily
    # * determine the final executable action.
    #
    # * Example:
    #
    # * youtube_pause
    # * youtube_resume
    # * youtube_next
    #
    # * If NCI does not provide one, the existing execution
    # * architecture remains responsible for resolving it.
    # * --------------------------------------------------------

    action: Optional[str] = None

    # * --------------------------------------------------------
    # * Strategy
    # * --------------------------------------------------------

    needs_ai: bool = False

    needs_action: bool = False

    needs_clarification: bool = False

    # * --------------------------------------------------------
    # AI instructions
    # * --------------------------------------------------------

    instructions: str = ""

    # * --------------------------------------------------------
    # * Metadata
    # * --------------------------------------------------------

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# * ============================================================
# * Builder
# * ============================================================

class ConversationRequestBuilder:

    """
    NCI-6 request builder.

    Takes:

        Natural Context
        Meaning Understanding
        Response Strategy

    and produces:

        ConversationRequest

    The resulting ConversationRequest is the common
    conversational representation used by later JARVIS
    integration layers.
    """

    # * --------------------------------------------------------

    @staticmethod
    def _value(
        source,
        name: str,
        default=None
    ):
        """
        Safely read an attribute from an NCI object.
        """

        if source is None:

            return default

        return getattr(
            source,
            name,
            default
        )

    # * --------------------------------------------------------

    @staticmethod
    def _list_value(
        source,
        name: str
    ) -> List[Any]:
        """
        Safely read a list-like attribute.

        Always returns a new list so the immutable
        ConversationRequest does not share mutable state
        with upstream NCI objects.
        """

        value = getattr(
            source,
            name,
            None
        ) if source is not None else None

        if value is None:

            return []

        if isinstance(value, (list, tuple, set)):

            return list(value)

        return [value]

    # * --------------------------------------------------------

    @staticmethod
    def _dict_value(
        source,
        name: str
    ) -> Dict[str, Any]:
        """
        Safely read a dictionary-like attribute.

        Always returns a new dictionary.
        """

        value = getattr(
            source,
            name,
            None
        ) if source is not None else None

        if isinstance(value, dict):

            return dict(value)

        return {}

    # * --------------------------------------------------------

    def build(
        self,
        *,
        user_input: str,
        meaning,
        strategy,
        context=None
    ) -> ConversationRequest:

        # * ====================================================
        # * Meaning
        # * ====================================================

        intent = self._value(
            meaning,
            "intent",
            "unknown"
        )

        confidence = float(
            self._value(
                meaning,
                "confidence",
                0.0
            )
        )

        # * ====================================================
        # * Relationship
        # * ====================================================

        relation = self._value(
            meaning,
            "relation",
            None
        )
        
        # * ----------------------------------------------------
        # * If meaning doesn't contain the relation,
        # * use the relation already established by the
        # * Conversation Coordinator.
        # * ----------------------------------------------------

        if relation is None and context is not None:

            relation = self._value(
                context,
                "relation"
            )

        # * Support enum-style relations safely.
        if hasattr(relation, "value"):

            relation = relation.value

        if relation is not None:

            relation = str(
                relation
            )

        # * ====================================================
        # * Action
        # * ====================================================

        action = self._value(
            meaning,
            "action",
            None
        )

        if action is not None:

            action = str(
                action
            )

        # * ====================================================
        # * References
        # * ====================================================

        references = self._list_value(
            meaning,
            "references"
        )

        # * Backward-compatible fallback:
        # * MeaningUnderstanding currently exposes a
        # * singular "reference" field.
        if not references:

            reference_value = self._value(
                meaning,
                "reference",
                None
            )

            if reference_value is not None:

                references = [
                    reference_value
                ]

        resolved_references = (
            self._dict_value(
                meaning,
                "resolved_references"
            )
        )

        unresolved_references = (
            self._list_value(
                meaning,
                "unresolved_references"
            )
        )

        # * ----------------------------------------------------
        # * Backward-compatible single reference
        #
        # * If NCI provides a single "reference" field,
        # * preserve it.
        #
        # * Otherwise derive it from the first detected
        # * reference when possible.
        # * ----------------------------------------------------

        reference = self._value(
            meaning,
            "reference",
            None
        )

        if reference is None and references:

            reference = references[0]

        # * ====================================================
        # * Strategy
        # * ====================================================

        mode = self._value(
            strategy,
            "mode",
            None
        )

        if hasattr(mode, "value"):

            mode = mode.value

        mode = (
            str(mode)
            if mode is not None
            else "conversation"
        )

        needs_ai = bool(
            self._value(
                strategy,
                "needs_ai",
                False
            )
        )

        needs_action = bool(
            self._value(
                strategy,
                "needs_action",
                False
            )
        )

        needs_clarification = bool(
            self._value(
                strategy,
                "needs_clarification",
                False
            )
        )

        # * ====================================================
        # * Context
        # * ====================================================

        topic = self._value(
            meaning,
            "topic"
        )

        task = self._value(
            meaning,
            "task"
        )

        object_value = self._value(
            meaning,
            "object"
        )

        application = self._value(
            meaning,
            "application"
        )

        skill = self._value(
            meaning,
            "skill"
        )

        # * ----------------------------------------------------
        # * If meaning doesn't contain context, use NCI context.
        # * ----------------------------------------------------

        if context is not None:

            topic = (
                topic
                or self._value(
                    context,
                    "topic"
                )
            )

            task = (
                task
                or self._value(
                    context,
                    "task"
                )
            )

            object_value = (
                object_value
                or self._value(
                    context,
                    "object"
                )
            )

            application = (
                application
                or self._value(
                    context,
                    "application"
                )
            )

            skill = (
                skill
                or self._value(
                    context,
                    "skill"
                )
            )

        # * ====================================================
        # * Instructions
        # * ====================================================

        instructions = (
            self._build_instructions(
                intent=intent,
                mode=mode,
                needs_ai=needs_ai,
                needs_action=needs_action,
                needs_clarification=(
                    needs_clarification
                ),
                topic=topic,
                task=task,
                object_value=object_value,
                reference=reference,
                application=application,
                skill=skill,
                action=action,
                relation=relation,
            )
        )

        # * ====================================================
        # * Metadata
        # * ====================================================

        metadata = {

            "builder":
                "ConversationRequestBuilder",

            "version":
                "1.1",

            "nci_stage":
                "NCI-6",

        }

        return ConversationRequest(

            user_input=user_input,

            relation=relation,

            intent=intent,

            mode=mode,

            confidence=confidence,

            topic=topic,

            task=task,

            object=object_value,

            reference=reference,

            references=references,

            resolved_references=(
                resolved_references
            ),

            unresolved_references=(
                unresolved_references
            ),

            application=application,

            skill=skill,

            action=action,

            needs_ai=needs_ai,

            needs_action=needs_action,

            needs_clarification=(
                needs_clarification
            ),

            instructions=instructions,

            metadata=metadata
        )

    # * ========================================================
    # * Instruction Builder
    # * ========================================================

    @staticmethod
    def _build_instructions(
        *,
        intent,
        mode,
        needs_ai,
        needs_action,
        needs_clarification,
        topic,
        task,
        object_value,
        reference,
        application,
        skill,
        action,
        relation,
    ) -> str:

        instructions = []

        # * ----------------------------------------------------
        # * Relationship
        # * ----------------------------------------------------

        if relation:

            instructions.append(
                f"Conversation relation: {relation}."
            )

        # * ----------------------------------------------------
        # * Conversation
        # * ----------------------------------------------------

        if mode == "conversation":

            instructions.append(
                "Respond naturally as part of "
                "the ongoing conversation."
            )

            if topic:

                instructions.append(
                    f"Current topic: {topic}."
                )

            if task:

                instructions.append(
                    f"Current task: {task}."
                )

            if object_value:

                instructions.append(
                    f"Current subject: {object_value}."
                )

            if reference:

                instructions.append(
                    f"The user referenced: {reference}."
                )

        # * ----------------------------------------------------
        # * Action
        # * ----------------------------------------------------

        elif mode == "action":

            instructions.append(
                "This request is primarily "
                "an executable action."
            )

            instructions.append(
                "Do not use AI reasoning when "
                "the existing execution system "
                "can handle the request."
            )

        # * ----------------------------------------------------
        # * Hybrid
        # * ----------------------------------------------------

        elif mode == "hybrid":

            instructions.append(
                "This request contains both "
                "an executable action and a "
                "conversational requirement."
            )

            instructions.append(
                "Preserve both parts of the request."
            )

        # * ----------------------------------------------------
        # * Clarification
        # * ----------------------------------------------------

        elif mode == "clarification":

            instructions.append(
                "The user needs clarification."
            )

            instructions.append(
                "Ask a concise clarification "
                "question before proceeding."
            )

        # * ----------------------------------------------------
        # * Application
        # * ----------------------------------------------------

        if application:

            instructions.append(
                f"Active application: {application}."
            )

        # * ----------------------------------------------------
        # * Skill
        # * ----------------------------------------------------

        if skill:

            instructions.append(
                f"Active skill: {skill}."
            )

        # * ----------------------------------------------------
        # * Action
        # * ----------------------------------------------------

        if action:

            instructions.append(
                f"Resolved action: {action}."
            )

        # * ----------------------------------------------------
        # AI requirement
        # * ----------------------------------------------------

        if needs_ai:

            instructions.append(
                "AI reasoning is required."
            )

        else:

            instructions.append(
                "AI reasoning is not required."
            )

        # * ----------------------------------------------------
        # * Action requirement
        # * ----------------------------------------------------

        if needs_action:

            instructions.append(
                "An executable action is required."
            )

        # * ----------------------------------------------------
        # * Clarification requirement
        # * ----------------------------------------------------

        if needs_clarification:

            instructions.append(
                "Additional clarification is required."
            )

        return " ".join(
            instructions
        )


# * ============================================================
# * Shared Builder
# * ============================================================

conversation_request_builder = (
    ConversationRequestBuilder()
)