"""
JARVIS PRO
Phase 11.3.2

Conversation Context

Maintains the active conversational context for the
current JARVIS session.

IMPORTANT:

This module does NOT execute commands.

It does NOT replace:
    - ConversationManager
    - ConversationStateManager
    - IntentEngine
    - Planner
    - Dispatcher
    - Skills
    - Memory

It only stores contextual information that can be used
by the Natural Conversation layer.

This allows JARVIS to understand things such as:

    "make it louder"
    "open the first one"
    "continue"
    "change that"
    "send it"
    "close it"

without modifying the existing execution architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, Optional


# * ============================================================
# * Conversation Context
# * ============================================================

@dataclass
class ConversationContext:

    # * --------------------------------------------------------
    # * Current conversational subject
    # * --------------------------------------------------------

    topic: Optional[str] = None

    # * --------------------------------------------------------
    # * Current task
    #
    # * Example:
    #
    # * "create python project"
    # * "search youtube"
    # * "play music"
    # * --------------------------------------------------------

    task: Optional[str] = None

    # * --------------------------------------------------------
    # * Current application / platform
    #
    # * Examples:
    #
    # * spotify
    # * chrome
    # * whatsapp
    # * youtube
    # * --------------------------------------------------------

    application: Optional[str] = None

    # * --------------------------------------------------------
    # * Current skill
    #
    # * Examples:
    #
    # * spotify
    # * whatsapp
    # * browser
    # * developer
    # * --------------------------------------------------------

    skill: Optional[str] = None

    # * --------------------------------------------------------
    # * Last detected intent
    # * --------------------------------------------------------

    intent: Optional[str] = None

    # * --------------------------------------------------------
    # * Last action
    # * --------------------------------------------------------

    action: Optional[str] = None

    # * --------------------------------------------------------
    # * Current object
    #
    # * Examples:
    #
    # * music
    # * file
    # * browser tab
    # * search result
    # * project
    # * message
    # * --------------------------------------------------------

    object: Optional[Any] = None

    # * --------------------------------------------------------
    # * Last referenced object
    #
    # * Used later for:
    #
    # * "it"
    # * "that"
    # * "the first one"
    # * --------------------------------------------------------
    
    objects: Optional[list[Any]] = None

    referenced_object: Optional[Any] = None

    # * --------------------------------------------------------
    # * Last result
    # * --------------------------------------------------------

    last_result: Optional[Any] = None

    # * --------------------------------------------------------
    # * Pending question
    #
    # * Example:
    #
    # * "Which platform?"
    # * "Who should I send it to?"
    # * --------------------------------------------------------

    pending_question: Optional[str] = None

    # * --------------------------------------------------------
    # * Pending clarification
    # * --------------------------------------------------------

    pending_clarification: Optional[str] = None

    # * --------------------------------------------------------
    # * Last user input
    # * --------------------------------------------------------

    last_user_input: Optional[str] = None

    # * --------------------------------------------------------
    # * Last assistant response
    # * --------------------------------------------------------

    last_assistant_response: Optional[str] = None

    # * --------------------------------------------------------
    # * Last relation detected by the conversation engine
    #
    # * Example:
    #
    # * follow_up
    # * correction
    # * reference
    # * confirmation
    # * --------------------------------------------------------

    last_relation: Optional[str] = None

    # * --------------------------------------------------------
    # * Context creation/update time
    # * --------------------------------------------------------

    updated_at: float = field(
        default_factory=time
    )


# * ============================================================
# * Conversation Context Manager
# * ============================================================

class ConversationContextManager:

    def __init__(self):

        self.context = ConversationContext()

    # * ========================================================
    # * Generic Update
    # * ========================================================

    def update(
        self,
        **kwargs
    ):

        """
        Update one or more context fields.

        Unknown fields are ignored intentionally.

        This prevents accidental creation of arbitrary state
        values that could later make the conversation system
        difficult to reason about.
        """

        valid_fields = {

            "topic",

            "task",

            "application",

            "skill",

            "intent",

            "action",

            "object",

            "objects",

            "referenced_object",

            "last_result",

            "pending_question",

            "pending_clarification",

            "last_user_input",

            "last_assistant_response",

            "last_relation",

        }

        for key, value in kwargs.items():

            if key not in valid_fields:
                continue

            setattr(
                self.context,
                key,
                value
            )

        self.context.updated_at = time()

    # * ========================================================
    # * User Input
    # * ========================================================

    def set_user_input(
        self,
        text: str
    ):

        self.context.last_user_input = text

        self.context.updated_at = time()

    # * ========================================================
    # * Assistant Response
    # * ========================================================

    def set_assistant_response(
        self,
        text: str
    ):

        self.context.last_assistant_response = text

        self.context.updated_at = time()

    # * ========================================================
    # * Relation
    # * ========================================================

    def set_relation(
        self,
        relation: str
    ):

        self.context.last_relation = relation

        self.context.updated_at = time()

    # * ========================================================
    # * Active Task
    # * ========================================================

    def set_task(
        self,
        task: Optional[str]
    ):

        self.context.task = task

        self.context.updated_at = time()

    # * ========================================================
    # * Topic
    # * ========================================================

    def set_topic(
        self,
        topic: Optional[str]
    ):

        self.context.topic = topic

        self.context.updated_at = time()

    # * ========================================================
    # * Application
    # * ========================================================

    def set_application(
        self,
        application: Optional[str]
    ):

        self.context.application = application

        self.context.updated_at = time()

    # * ========================================================
    # * Skill
    # * ========================================================

    def set_skill(
        self,
        skill: Optional[str]
    ):

        self.context.skill = skill

        self.context.updated_at = time()

    # * ========================================================
    # * Intent
    # * ========================================================

    def set_intent(
        self,
        intent: Optional[str]
    ):

        self.context.intent = intent

        self.context.updated_at = time()

    # * ========================================================
    # * Action
    # * ========================================================

    def set_action(
        self,
        action: Optional[str]
    ):

        self.context.action = action

        self.context.updated_at = time()

    # * ========================================================
    # * Object
    # * ========================================================

    def set_object(
        self,
        obj: Optional[Any]
    ):

        self.context.object = obj

        self.context.updated_at = time()

    # * ========================================================
    # * Referenced Object
    # * ========================================================

    def set_referenced_object(
        self,
        obj: Optional[Any]
    ):

        self.context.referenced_object = obj

        self.context.updated_at = time()

    # * ========================================================
    # * Last Result
    # * ========================================================

    def set_last_result(
        self,
        result: Optional[Any]
    ):

        self.context.last_result = result

        self.context.updated_at = time()

    # * ========================================================
    # * Pending Question
    # * ========================================================

    def set_pending_question(
        self,
        question: Optional[str]
    ):

        self.context.pending_question = question

        self.context.updated_at = time()

    # * ========================================================
    # * Pending Clarification
    # * ========================================================

    def set_pending_clarification(
        self,
        clarification: Optional[str]
    ):

        self.context.pending_clarification = clarification

        self.context.updated_at = time()

    # * ========================================================
    # * Get Context
    # * ========================================================

    def get_context(self) -> ConversationContext:

        return self.context

    # * ========================================================
    # * Get Value
    # * ========================================================

    def get(
        self,
        key: str,
        default=None
    ):

        return getattr(
            self.context,
            key,
            default
        )

    # * ========================================================
    # * Has Active Context
    # * ========================================================

    def has_context(self) -> bool:

        fields = [

            self.context.topic,

            self.context.task,

            self.context.application,

            self.context.skill,

            self.context.intent,

            self.context.action,

            self.context.object,

            self.context.pending_question,

            self.context.pending_clarification,

        ]

        return any(
            value is not None
            for value in fields
        )

    # * ========================================================
    # * Clear Pending Conversation
    # * ========================================================

    def clear_pending(self):

        self.context.pending_question = None

        self.context.pending_clarification = None

        self.context.updated_at = time()

    # * ========================================================
    # * Clear Active Task
    # * ========================================================

    def clear_task(self):

        self.context.task = None

        self.context.intent = None

        self.context.action = None

        self.context.pending_question = None

        self.context.pending_clarification = None

        self.context.updated_at = time()

    # * ========================================================
    # * Clear Context
    # * ========================================================

    def clear(self):

        self.context = ConversationContext()

    # * ========================================================
    # * Snapshot
    # * ========================================================

    def snapshot(self) -> dict:

        return {

            "topic": self.context.topic,

            "task": self.context.task,

            "application": self.context.application,

            "skill": self.context.skill,

            "intent": self.context.intent,

            "action": self.context.action,

            "object": self.context.object,

            "objects": self.context.objects,

            "referenced_object":
                self.context.referenced_object,

            "last_result":
                self.context.last_result,

            "pending_question":
                self.context.pending_question,

            "pending_clarification":
                self.context.pending_clarification,

            "last_user_input":
                self.context.last_user_input,

            "last_assistant_response":
                self.context.last_assistant_response,

            "last_relation":
                self.context.last_relation,

            "updated_at":
                self.context.updated_at,

        }

    # * ========================================================
    # ! Debug Representation
    # * ========================================================

    def info(self) -> dict:

        return self.snapshot()

    def __repr__(self):

        return (
            "<ConversationContextManager "
            f"topic={self.context.topic!r} "
            f"task={self.context.task!r} "
            f"application={self.context.application!r} "
            f"skill={self.context.skill!r}>"
        )


# * ============================================================
# * Shared Context Instance
# * ============================================================

conversation_context = ConversationContextManager()


# * ============================================================
# * Convenience Functions
# * ============================================================

def get_context() -> ConversationContext:

    return conversation_context.get_context()


def get(
    key: str,
    default=None
):

    return conversation_context.get(
        key,
        default
    )


def update(**kwargs):

    conversation_context.update(
        **kwargs
    )


def clear():

    conversation_context.clear()