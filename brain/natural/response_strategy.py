"""
JARVIS PRO
Natural Conversation Intelligence

NCI-5: Response Strategy

Determines HOW JARVIS should handle an understood request.

This layer does NOT execute anything.

It only decides:

    - conversation
    - action
    - hybrid
    - clarification

and whether AI reasoning is useful.
"""

from dataclasses import dataclass
from enum import Enum


_TECHNICAL_ERROR_MARKERS = (
    "traceback",
    "connectionerror",
    "timeouterror",
    "requests.exceptions",
    "httpx.",
    "filenotfounderror",
    "permissionerror",
    "oserror",
    "winerror",
    "exception(",
    " at 0x",
)


def _safe_result_text(value):
    """Return only plain user-facing text from an action result value."""

    if not isinstance(value, str):
        return None

    text = value.strip()
    return text or None


def _natural_failure_message(error):
    """Hide implementation-level failures while retaining useful wording."""

    error_text = _safe_result_text(error)
    if not error_text:
        return "I couldn't complete that request."

    lowered = error_text.lower()
    if any(marker in lowered for marker in _TECHNICAL_ERROR_MARKERS):
        if any(
            marker in lowered
            for marker in (
                "connectionerror",
                "timeouterror",
                "requests.exceptions",
                "httpx.",
                "connection",
                "timeout",
            )
        ):
            return (
                "I couldn't connect to the service. "
                "Check that it is running and try again."
            )
        return "I couldn't complete that request."

    return error_text


def _natural_success_message(action_name, action_data):
    """Provide a concise fallback when a successful action has no message."""

    if action_name == "open" and isinstance(action_data, dict):
        app = _safe_result_text(action_data.get("app"))
        if app:
            return f"{app.title()} is open."

    return "Done."


def action_result_message(
    action_name,
    action_data=None,
    result=None,
):
    """Return a user-facing action result without exposing raw structures.

    Skills remain responsible for their own rich narration. This helper is
    only for the existing dispatcher fallback when an action returns a
    message-bearing value and has not already spoken it.
    """

    if result is None:
        return None

    if isinstance(result, dict):
        success = result.get("success")
        status = str(result.get("status", "")).strip().lower()

        if success is False or status in {"error", "failed", "failure"}:
            return _natural_failure_message(
                result.get("error") or result.get("message")
            )

        message = _safe_result_text(result.get("message"))
        if message:
            return message

        nested_result = _safe_result_text(result.get("result"))
        if nested_result:
            return nested_result

        nested_data = _safe_result_text(result.get("data"))
        if nested_data:
            return nested_data

        if success is True or status in {"ok", "success", "completed"}:
            return _natural_success_message(action_name, action_data)

        if result.get("error") is not None:
            return _natural_failure_message(result.get("error"))

        return None

    if isinstance(result, str):
        return _natural_failure_message(result) if any(
            marker in result.lower()
            for marker in _TECHNICAL_ERROR_MARKERS
        ) else _safe_result_text(result)

    return None


# * ============================================================
# * Response Mode
# * ============================================================

class ResponseMode(Enum):

    CONVERSATION = "conversation"

    ACTION = "action"

    HYBRID = "hybrid"

    CLARIFICATION = "clarification"


# * ============================================================
# * Response Strategy
# * ============================================================

@dataclass(frozen=True)
class ResponseStrategy:

    mode: ResponseMode

    needs_action: bool

    needs_ai: bool

    needs_clarification: bool

    intent: str

    confidence: float

    reason: str


# * ============================================================
# * NCI-5 Engine
# * ============================================================

class ResponseStrategyEngine:

    def decide(self, meaning):

        # * ====================================================
        # * Clarification
        # * ====================================================

        if meaning.intent == "clarification":

            return ResponseStrategy(

                mode=ResponseMode.CLARIFICATION,

                needs_action=False,

                needs_ai=False,

                needs_clarification=True,

                intent=meaning.intent,

                confidence=0.94,

                reason=(
                    "The user is requesting "
                    "clarification."
                ),
            )

        # * ====================================================
        # * Hybrid
        # * ====================================================

        if meaning.intent == "hybrid_request":

            return ResponseStrategy(

                mode=ResponseMode.HYBRID,

                needs_action=True,

                needs_ai=True,

                needs_clarification=False,

                intent=meaning.intent,

                confidence=0.93,

                reason=(
                    "The request contains both "
                    "an executable action and "
                    "a conversational requirement."
                ),
            )

        # * ====================================================
        # * Explicit action
        # * ====================================================

        if meaning.mode.value == "action":

            return ResponseStrategy(

                mode=ResponseMode.ACTION,

                needs_action=True,

                needs_ai=False,

                needs_clarification=False,

                intent=meaning.intent,

                confidence=0.94,

                reason=(
                    "The request is an executable "
                    "action and does not require "
                    "conversational reasoning."
                ),
            )

        # * ====================================================
        # * Conversation
        # * ====================================================

        if meaning.mode.value == "conversation":

            return ResponseStrategy(

                mode=ResponseMode.CONVERSATION,

                needs_action=False,

                needs_ai=True,

                needs_clarification=False,

                intent=meaning.intent,

                confidence=0.94,

                reason=(
                    "The request requires a "
                    "natural conversational response."
                ),
            )

        # * ====================================================
        # * Safe fallback
        # * ====================================================

        return ResponseStrategy(

            mode=ResponseMode.CONVERSATION,

            needs_action=False,

            needs_ai=True,

            needs_clarification=False,

            intent=(
                meaning.intent
                or "unknown"
            ),

            confidence=0.60,

            reason=(
                "No specific response strategy "
                "was identified."
            ),
        )


# * ============================================================
# * Shared engine
# * ============================================================

response_strategy_engine = (
    ResponseStrategyEngine()
)
