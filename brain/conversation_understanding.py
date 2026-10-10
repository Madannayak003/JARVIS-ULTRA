"""
JARVIS PRO
Phase 11.3.1

Conversation Understanding Core

Determines the relationship between the current
user input and the existing conversation.

IMPORTANT:
This module does NOT execute commands.
It does NOT replace IntentEngine.
It does NOT replace ConversationManager.
It does NOT replace ConversationStateManager.

It only provides conversational understanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re


# * ============================================================
# * Conversation Relationship
# * ============================================================

class ConversationRelation(str, Enum):

    NEW_REQUEST = "new_request"

    FOLLOW_UP = "follow_up"

    CLARIFICATION_ANSWER = "clarification_answer"

    CORRECTION = "correction"

    CONFIRMATION = "confirmation"

    REJECTION = "rejection"

    CANCELLATION = "cancellation"

    REFERENCE = "reference"

    CONTINUATION = "continuation"

    CHAT = "chat"

    UNKNOWN = "unknown"


# * ============================================================
# * Understanding Result
# * ============================================================

@dataclass
class ConversationUnderstanding:

    relation: ConversationRelation

    confidence: float = 0.0

    reason: str = ""

    raw_input: str = ""

    # * Contextual references found in the input.
    #
    # * Examples:
    #
    # * "make it louder"
    # * -> ["it"]
    #
    # * "open the first one"
    # * -> ["the first one"]
    #
    references: list[str] = field(
        default_factory=list
    )


# * ============================================================
# * Conversation Understanding Engine
# * ============================================================

class ConversationUnderstandingEngine:

    def __init__(self):

        # * ----------------------------------------------------
        # * Confirmation phrases
        #
        # ! IMPORTANT:
        # * Existing confirmation.py remains authoritative
        # * during real JARVIS execution.
        #
        # * This list is only for understanding/classification.
        # * ----------------------------------------------------

        self.confirmation_phrases = {
            "yes",
            "yes sir",
            "yes please",
            "sure",
            "okay",
            "ok",
            "confirm",
            "confirmed",
            "do it",
            "go ahead",
            "yes continue",
            "yes do it",
            "yes switch",
        }

        # * ----------------------------------------------------
        # * Rejection phrases
        # * ----------------------------------------------------

        self.rejection_phrases = {
            "no",
            "no thanks",
            "don't",
            "dont",
            "nope",
            "not now",
        }

        # * ----------------------------------------------------
        # * Cancellation phrases
        # * ----------------------------------------------------

        self.cancellation_phrases = {
            "cancel",
            "cancel it",
            "never mind",
            "nevermind",
            "forget it",
            "stop",
            "stop it",
            "don't do it",
            "dont do it",
        }

        # * ----------------------------------------------------
        # * Continuation phrases
        #
        # * "continue" is intentionally NOT inside the
        # * confirmation list.
        #
        # * Existing confirmation handling in core.assistant
        # * still has priority when JARVIS is waiting.
        # * ----------------------------------------------------

        self.continuation_phrases = {
            "continue",
            "continue that",
            "continue it",
            "keep going",
            "go on",
            "carry on",
            "resume",
            "resume it",
            "again",
            "do that again",
        }

        # * ----------------------------------------------------
        # * Correction indicators
        # * ----------------------------------------------------

        self.correction_patterns = [

            r"^actually\b",

            r"^instead\b",

            r"^no,?\s+",

            r"^wait\b",

            r"^wait,",

            r"^i meant\b",

            r"^i mean\b",

            r"^change that\b",

            r"^make that\b",

        ]

        # * ----------------------------------------------------
        # * Reference patterns
        #
        # * These are NOT automatically the main relation.
        #
        # * Example:
        #
        # * "make it louder"
        #
        # * relation   = FOLLOW_UP
        # * references = ["it"]
        # * ----------------------------------------------------

        self.reference_patterns = [

            (r"\bit\b", "it"),

            (r"\bthis\b", "this"),

            (r"\bthat\b", "that"),

            (r"\bthese\b", "these"),

            (r"\bthose\b", "those"),

            (r"\bthe first one\b", "the first one"),

            (r"\bthe second one\b", "the second one"),

            (r"\bthe last one\b", "the last one"),

            (r"\bthe previous one\b", "the previous one"),

            (r"\bthe same one\b", "the same one"),

            (r"\bsame\b", "same"),

        ]

        # * ----------------------------------------------------
        # * Follow-up indicators
        #
        # ! IMPORTANT:
        #
        # * Generic commands such as:
        #
        # * open
        # * play
        # * pause
        # * close
        # * search
        # * send
        #
        # * are NOT placed here because they can be completely
        # * valid NEW_REQUEST commands.
        # * ----------------------------------------------------

        self.follow_up_patterns = [

            r"^and\b",

            r"^also\b",

            r"^then\b",

            r"^now\b",

            r"^next\b",

            r"^make\b",

            r"^change\b",

            r"^increase\b",

            r"^decrease\b",

            r"^lower\b",

            r"^raise\b",

            r"^add\b",

            r"^remove\b",

        ]

    # * ========================================================
    # * Public API
    # * ========================================================

    def understand(
        self,
        user_input: str,
        previous_messages=None,
        state=None,
    ) -> ConversationUnderstanding:

        raw_input = user_input or ""

        text = self._normalize(raw_input)

        # * ----------------------------------------------------
        # * Empty input
        # * ----------------------------------------------------

        if not text:

            return self._result(
                relation=ConversationRelation.UNKNOWN,
                confidence=1.0,
                reason="Empty input.",
                raw_input=raw_input,
            )

        # * ----------------------------------------------------
        # * Extract references FIRST.
        #
        # * Reference information is kept separately from the
        # * main conversational relationship.
        # * ----------------------------------------------------

        references = self._extract_references(text)

        # * ====================================================
        # * CANCELLATION
        # * ====================================================

        if text in self.cancellation_phrases:

            return self._result(
                relation=ConversationRelation.CANCELLATION,
                confidence=0.99,
                reason="Input matches a cancellation phrase.",
                raw_input=raw_input,
                references=references,
            )

        # * ====================================================
        # * CONTINUATION
        # * ====================================================

        if text in self.continuation_phrases:

            return self._result(
                relation=ConversationRelation.CONTINUATION,
                confidence=0.98,
                reason="Input matches a continuation phrase.",
                raw_input=raw_input,
                references=references,
            )

        # * ====================================================
        # * CORRECTION
        # * ====================================================

        if self._matches_any(
            text,
            self.correction_patterns
        ):

            return self._result(
                relation=ConversationRelation.CORRECTION,
                confidence=0.95,
                reason="Input contains a correction indicator.",
                raw_input=raw_input,
                references=references,
            )

        # * ====================================================
        # * CONFIRMATION
        # * ====================================================

        if text in self.confirmation_phrases:

            return self._result(
                relation=ConversationRelation.CONFIRMATION,
                confidence=0.99,
                reason="Input matches a confirmation phrase.",
                raw_input=raw_input,
                references=references,
            )

        # * ====================================================
        # * REJECTION
        # * ====================================================

        if text in self.rejection_phrases:

            return self._result(
                relation=ConversationRelation.REJECTION,
                confidence=0.99,
                reason="Input matches a rejection phrase.",
                raw_input=raw_input,
                references=references,
            )

        # * ====================================================
        # * CONTEXT-AWARE CLARIFICATION
        #
        # * This check happens before generic follow-up logic.
        #
        # * If JARVIS is explicitly waiting for an answer and
        # * the user gives a short response such as:
        #
        # * "Rahul"
        # * "Chrome"
        # * "Google"
        #
        # * it can be treated as a clarification answer.
        #
        # * Existing confirmation/WhatsApp logic still has
        # * priority in the real assistant loop.
        # * ====================================================

        if self._has_waiting_state(state):

            if self._looks_like_short_answer(text):

                return self._result(
                    relation=ConversationRelation.CLARIFICATION_ANSWER,
                    confidence=0.70,
                    reason=(
                        "Short response while conversation "
                        "state is waiting."
                    ),
                    raw_input=raw_input,
                    references=references,
                )

        # * ====================================================
        # * FOLLOW-UP
        #
        # * This is checked AFTER explicit conversation states.
        #
        # * Example:
        #
        # * "make it louder"
        #
        # * becomes:
        #
        # * relation   = FOLLOW_UP
        # * references = ["it"]
        # * ====================================================

        if self._matches_any(
            text,
            self.follow_up_patterns
        ):

            return self._result(
                relation=ConversationRelation.FOLLOW_UP,
                confidence=0.80,
                reason="Input resembles a conversational follow-up.",
                raw_input=raw_input,
                references=references,
            )

        # * ====================================================
        # * REFERENCE ONLY
        #
        # * If the input contains a contextual reference but
        # * does not otherwise look like a follow-up, preserve
        # * REFERENCE as the relationship.
        #
        # * Example:
        #
        # * "the first one"
        # * ====================================================

        if references:

            return self._result(
                relation=ConversationRelation.REFERENCE,
                confidence=0.85,
                reason="Input contains a contextual reference.",
                raw_input=raw_input,
                references=references,
            )
            
        # * ====================================================
        # * CONTEXTUAL ACTION
        #
        # * Some commands are valid standalone commands but
        # * become conversational continuations when the active
        # * context matches the application.
        #
        # * Example:
        #
        # * search ESP32 on YouTube
        # * play the first video
        #
        # * The second command remains a normal command at the
        # * router level, but Natural Conversation understands
        # * that it continues the active YouTube task.
        # * ====================================================

        contextual_relation = (
            self._contextual_action_relation(
                text,
                state,
            )
        )

        if contextual_relation:

            return self._result(
                relation=contextual_relation,
                confidence=0.92,
                reason=(
                    "Input matches a contextual action "
                    "for the active application."
                ),
                raw_input=raw_input,
                references=references,
            )

        # * ====================================================
        # * NEW REQUEST
        # * ====================================================

        # * ====================================================
        # * NEW REQUEST
        # * ====================================================

        return self._result(
            relation=ConversationRelation.NEW_REQUEST,
            confidence=0.60,
            reason=(
                "No strong conversational relationship "
                "detected."
            ),
            raw_input=raw_input,
            references=references,
        )

    # * ========================================================
    # * Normalize
    # * ========================================================

    @staticmethod
    def _normalize(
        text: str
    ) -> str:

        text = text.lower().strip()

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    # * ========================================================
    # * Pattern Matching
    # * ========================================================

    @staticmethod
    def _matches_any(
        text: str,
        patterns
    ) -> bool:

        for pattern in patterns:

            if re.search(
                pattern,
                text
            ):

                return True

        return False

    # * ========================================================
    # * Reference Extraction
    # * ========================================================

    @staticmethod
    def _extract_references(
        text: str
    ) -> list[str]:

        references = []

        reference_patterns = [

            (r"\bit\b", "it"),

            (r"\bthis\b", "this"),

            (r"\bthat\b", "that"),

            (r"\bthese\b", "these"),

            (r"\bthose\b", "those"),

            (
                r"\b(?:the\s+)?first one\b",
                "the first one"
            ),

            (
                r"\b(?:the\s+)?second one\b",
                "the second one"
            ),

            (
                r"\b(?:the\s+)?third one\b",
                "the third one"
            ),

            (
                r"\b(?:the\s+)?fourth one\b",
                "the fourth one"
            ),

            (
                r"\b(?:the\s+)?fifth one\b",
                "the fifth one"
            ),

            (
                r"\b(?:the\s+)?sixth one\b",
                "the sixth one"
            ),

            (
                r"\bnumber one\b",
                "number one"
            ),

            (
                r"\bnumber two\b",
                "number two"
            ),

            (
                r"\bnumber three\b",
                "number three"
            ),

            (
                r"\bnumber four\b",
                "number four"
            ),

            (
                r"\bnumber five\b",
                "number five"
            ),

            (
                r"\bthe last one\b",
                "the last one"
            ),

            (
                r"\bthe previous one\b",
                "the previous one"
            ),

            (
                r"\bthe same one\b",
                "the same one"
            ),

            (
                r"\bsame\b",
                "same"
            ),
        ]

        for pattern, value in reference_patterns:

            if re.search(
                pattern,
                text
            ):

                references.append(value)

        return references

    # * ========================================================
    # * Reference Position
    #
    # * Converts a recognized positional reference into a
    # * one-based position.
    #
    # * This method does NOT access BrowserContext.
    # * ========================================================

    @staticmethod
    def reference_position(
        reference: str,
    ) -> int | None:

        positions = {

            "the first one": 1,
            "the second one": 2,
            "the third one": 3,
            "the fourth one": 4,
            "the fifth one": 5,
            "the sixth one": 6,

            "number one": 1,
            "number two": 2,
            "number three": 3,
            "number four": 4,
            "number five": 5,

        }

        return positions.get(
            reference.strip().lower()
        )

    # * ========================================================
    # * Waiting State
    # * ========================================================

    @staticmethod
    def _has_waiting_state(
        state
    ) -> bool:

        if state is None:

            return False

        try:

            # * --------------------------------------------
            # * ConversationStateManager
            # * --------------------------------------------

            if hasattr(
                state,
                "is_waiting"
            ):

                return state.is_waiting()

            # * --------------------------------------------
            # * Dictionary state
            # * --------------------------------------------

            if isinstance(
                state,
                dict
            ):

                return bool(
                    state.get("waiting")
                )

        except Exception:

            # ! Conversation understanding must NEVER crash
            # * the main JARVIS runtime because of a state
            # * lookup problem.
            return False

        return False

    # * ========================================================
    # * Short Answer Detection
    # * ========================================================

    @staticmethod
    def _looks_like_short_answer(
        text: str
    ) -> bool:

        words = text.split()

        return len(words) <= 6
    
    # * ========================================================
    # * Contextual Action Detection
    #
    # * Some commands are valid standalone NEW_REQUEST commands
    # * but become conversational continuations when an active
    # * application/task already exists.
    #
    # * Example:
    #
    # * search ESP32 on YouTube
    # * play the first video
    #
    # * "play the first video" is a valid standalone command,
    # ! so it must NOT globally become FOLLOW_UP.
    #
    # * It becomes CONTINUATION only when the active context
    # * indicates YouTube.
    # * ========================================================

    @staticmethod
    def _contextual_action_relation(
        text: str,
        state,
    ):
        """
        Detect commands that should be treated as
        conversational continuations only when the
        active context supports them.

        Returns:
            ConversationRelation | None
        """

        if state is None:
            return None

        # * ----------------------------------------------------
        # * Read active context safely
        # * ----------------------------------------------------

        application = None
        skill = None
        topic = None

        try:

            # * ConversationContextManager
            if hasattr(
                state,
                "application"
            ):
                application = state.application

            if hasattr(
                state,
                "skill"
            ):
                skill = state.skill

            if hasattr(
                state,
                "topic"
            ):
                topic = state.topic

            # * Snapshot fallback
            if hasattr(
                state,
                "snapshot"
            ):

                snapshot = state.snapshot()

                if isinstance(snapshot, dict):

                    application = (
                        application
                        or snapshot.get("application")
                    )

                    skill = (
                        skill
                        or snapshot.get("skill")
                    )

                    topic = (
                        topic
                        or snapshot.get("topic")
                    )

        except Exception:

            # ! Natural conversation must never break
            # * normal JARVIS execution.
            return None

        application = str(
            application or ""
        ).strip().lower()

        skill = str(
            skill or ""
        ).strip().lower()

        topic = str(
            topic or ""
        ).strip().lower()

        # * ====================================================
        # * YouTube contextual actions
        # * ====================================================

        youtube_context = (
            application == "youtube"
            or skill == "youtube"
            or topic == "video"
        )

        if youtube_context:

            youtube_continuations = {

                "play first video",

                "play the first video",

                "play first youtube video",

                "play the first youtube video",
                
                "play next one",

                "play the next one",

                "play next video",

                "play the next video",

                "next video",
                
                "resume",

                "resume video",
                
                "continue video",
                
                "continue youtube",

                "previous video",

                "play previous video",

                "play the previous video",
            }

            if text in youtube_continuations:

                return (
                    ConversationRelation.CONTINUATION
                )

        # * ====================================================
        # * Spotify contextual actions
        # * ====================================================

        spotify_context = (
            application == "spotify"
            or skill == "spotify"
            or topic == "music"
        )

        if spotify_context:

            spotify_continuations = {

                "play next song",

                "play the next song",

                "next song",

                "previous song",

                "play previous song",

                "play the previous song",
            }

            if text in spotify_continuations:

                return (
                    ConversationRelation.CONTINUATION
                )

        return None

    # * ========================================================
    # * Result Builder
    # * ========================================================

    @staticmethod
    def _result(
        relation,
        confidence,
        reason,
        raw_input,
        references=None,
    ) -> ConversationUnderstanding:

        return ConversationUnderstanding(

            relation=relation,

            confidence=confidence,

            reason=reason,

            raw_input=raw_input,

            references=references or [],

        )


# * ============================================================
# * Shared Engine
# * ============================================================

conversation_understanding = (
    ConversationUnderstandingEngine()
)


# * ============================================================
# * Convenience Function
# * ============================================================

def understand(
    user_input: str,
    previous_messages=None,
    state=None,
) -> ConversationUnderstanding:

    return conversation_understanding.understand(

        user_input=user_input,

        previous_messages=previous_messages,

        state=state,

    )
