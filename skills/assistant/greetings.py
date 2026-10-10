"""
JARVIS PRO greeting skill.

The skill keeps startup speech separate from user-triggered greetings. Startup
speech is generated locally from a small set of coherent, time-aware styles;
it never calls an AI service and never runs while this module is imported.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Mapping

from core.registry import register
from config.settings import get_assistant_display_name
from core.diagnostics import debug_print


# * ---------------------------------------------------------------------------
# * Backward-compatible response collections
# * ---------------------------------------------------------------------------

GREETINGS = (
    "Hello. What shall we work on?",
    "Hi there. How can I help?",
    "Hey. What are we working on today?",
    "Good to hear from you. What can I do?",
)

HOW_ARE_YOU = (
    "I'm doing well, thanks for asking. What can I help with?",
    "I'm well and ready to help. What's on your mind?",
    "Doing well. What would you like to work on?",
)

WELCOME = (
    "Anytime. Glad I could help.",
    "You're welcome. Happy to help.",
    "My pleasure.",
)

BYE = (
    "Goodbye. Take care.",
    "See you later. Have a good one.",
    "Goodbye. I'll be here when you need me.",
)


@dataclass(frozen=True)
class _StartupVariant:
    """One complete startup utterance, rather than a sentence fragment."""

    text: str
    uses_name: bool = False

    def render(self, name: str | None = None) -> str:
        name_suffix = f", {name}" if self.uses_name and name else ""
        return self.text.format(name=name_suffix)


# * Styles are deliberately complete utterances. The engine chooses one style
# * per context, so it does not produce an awkward stack of random fragments.
STARTUP = {
    "morning": (
        _StartupVariant("Good morning{name}. Ready to get started?", True),
        _StartupVariant(
            "Good morning. Good to have you back. What are we working on?"
        ),
        _StartupVariant(
            "Good morning{name}. I’m here when you’re ready to begin.", True
        ),
        _StartupVariant("Good morning. Let’s make a useful start to the day."),
    ),
    "afternoon": (
        _StartupVariant("Good afternoon{name}. What shall we work on?", True),
        _StartupVariant(
            "Good afternoon. Welcome back. Ready when you are."
        ),
        _StartupVariant(
            "Good afternoon{name}. I’m ready whenever you are.", True
        ),
        _StartupVariant("Good afternoon. What would you like to tackle?"),
    ),
    "evening": (
        _StartupVariant("Good evening{name}. What are we working on tonight?", True),
        _StartupVariant(
            "Good evening. Good to have you back. Where shall we begin?"
        ),
        _StartupVariant(
            "Good evening{name}. Everything’s ready when you are.", True
        ),
        _StartupVariant("Good evening. What can I help you make progress on?"),
    ),
    "night": (
        _StartupVariant("Good evening{name}. Still time for one more thing?", True),
        _StartupVariant("Good evening. I’m here if you need a hand tonight."),
        _StartupVariant("It’s a late one, but we can keep this focused."),
        _StartupVariant("Good evening. Ready when you are."),
    ),
}


_USER_GREETING_STYLES = {
    "general": GREETINGS,
    "morning": (
        "Good morning. I hope your day is off to a good start.",
        "Good morning. What can I help you with?",
    ),
    "afternoon": (
        "Good afternoon. How can I help?",
        "Good afternoon. What shall we work on?",
    ),
    "evening": (
        "Good evening. What can I help you with?",
        "Good evening. How has your day been?",
    ),
}


class GreetingEngine:
    """Small in-memory selector that avoids immediate repetition."""

    def __init__(self):
        self._last_selected = {}

    def reset(self):
        """Clear in-memory variation state, primarily useful for tests."""

        self._last_selected.clear()

    def _choose(self, group: str, options):
        options = tuple(options)
        previous = self._last_selected.get(group)
        candidates = tuple(option for option in options if option != previous)
        selected = random.choice(candidates or options)
        self._last_selected[group] = selected
        return selected

    def startup(self, context: str, name: str | None = None) -> str:
        variant = self._choose(f"startup:{context}", STARTUP[context])
        return variant.render(name)

    def user_greeting(self, style: str = "general") -> str:
        return self._choose(
            f"user:{style}",
            _USER_GREETING_STYLES.get(style, GREETINGS),
        )

    def response(self, group: str, options) -> str:
        return self._choose(group, options)


_engine = GreetingEngine()
_startup_lock = Lock()
_startup_spoken = False


def _time_context(now: datetime | None = None) -> str:
    """Return the existing four-part time context used by JARVIS."""

    hour = (now or datetime.now()).hour

    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 22:
        return "evening"
    return "night"


def _preferred_name(profile=None) -> str | None:
    """Read only the existing profile name, failing closed when unavailable."""

    if profile is None:
        try:
            # * Lazy import avoids profile/file work while the skill is loaded.
            from brain import profile as profile_manager

            profile = profile_manager
        except Exception:
            return None

    try:
        if isinstance(profile, Mapping):
            value = profile.get("name", "")
        elif hasattr(profile, "get"):
            value = profile.get("name", "")
        else:
            value = getattr(profile, "name", "")

        if isinstance(value, str):
            value = value.strip()
            return value or None
    except Exception:
        pass

    return None


def _fallback_startup(context: str, name: str | None = None) -> str:
    opening = {
        "morning": "Good morning",
        "afternoon": "Good afternoon",
        "evening": "Good evening",
        "night": "Good evening",
    }.get(context, "Hello")

    if name:
        opening += f", {name}"

    return f"{opening}. Ready when you are."


def startup_greeting(now: datetime | None = None, profile=None) -> str:
    """Build one concise startup utterance from local time and profile data."""

    context = "evening"

    try:
        context = _time_context(now)
        name = _preferred_name(profile)
        print(f"[GREETING] Startup context: {context}")
        greeting = _engine.startup(context, name)
    except Exception as error:
        # ! Greeting generation is never allowed to block JARVIS startup.
        print(f"[GREETING] Startup selection failed safely: {error}")
        greeting = _fallback_startup(context, _preferred_name(profile))

    print("[GREETING] Startup greeting selected")
    return greeting or _fallback_startup(context)


def startup_brief_greeting(now: datetime | None = None, profile=None) -> str:
    """Return the existing time-aware greeting as a concise opening."""
    context = _time_context(now)
    name = _preferred_name(profile)
    opening = {
        "morning": "Good morning",
        "afternoon": "Good afternoon",
        "evening": "Good evening",
        "night": "Good evening",
    }.get(context, "Hello")
    return f"{opening}{f', {name}' if name else ''}."


def _get_speaker():
    """Load the established TTS entry point only when speech is requested."""

    from voice.manager import speak

    return speak


def speak_startup_greeting(speaker=None, profile=None, now=None) -> bool:
    """Speak startup greeting once for the current initialization lifecycle."""

    global _startup_spoken

    with _startup_lock:
        if _startup_spoken:
            return False

        # * Mark before TTS so concurrent/re-entrant startup calls cannot speak
        # ! twice. A failed TTS call must not cause a startup retry storm.
        _startup_spoken = True

        try:
            greeting = startup_greeting(now=now, profile=profile)
        except Exception as error:
            print(f"[GREETING] Startup fallback engaged: {error}")
            greeting = (
                f"Hello. {get_assistant_display_name()} is ready when you are."
            )

    try:
        (speaker or _get_speaker())(greeting)
    except Exception as error:
        print(f"[GREETING] Startup speech failed safely: {error}")
        return False

    print("[GREETING] Startup greeting spoken")
    return True


def speak_startup_text(speaker, text: str) -> bool:
    """Speak coordinator output using the existing one-shot lifecycle guard."""
    global _startup_spoken
    with _startup_lock:
        if _startup_spoken:
            return False
        _startup_spoken = True
    try:
        (speaker or _get_speaker())(text or _fallback_startup(_time_context()))
    except Exception as error:
        print(f"[GREETING] Startup speech failed safely: {error}")
        return False
    debug_print("[GREETING] Startup brief spoken")
    return True


def _command_text(data) -> str:
    if not isinstance(data, Mapping):
        return ""
    value = data.get("command", "")
    return str(value).strip().lower().rstrip("?!.,")


def _speak(text: str) -> None:
    try:
        _get_speaker()(text)
    except Exception as error:
        print(f"[GREETING] Speech failed safely: {error}")


# * ---------------------------------------------------------------------------
# * Registered user-facing skill actions
# * ---------------------------------------------------------------------------

def greet(data):
    command = _command_text(data)

    if command.startswith("good morning"):
        message = _engine.user_greeting("morning")
    elif command.startswith("good afternoon"):
        message = _engine.user_greeting("afternoon")
    elif command.startswith("good evening"):
        message = _engine.user_greeting("evening")
    else:
        message = _engine.user_greeting("general")

    _speak(message)
    return True


def how_are_you(data):
    _speak(_engine.response("how_are_you", HOW_ARE_YOU))
    return True


def assistant_name(data):
    _speak(f"I am {get_assistant_display_name()}, your desktop AI assistant.")
    return True


def welcome(data):
    _speak(_engine.response("welcome", WELCOME))
    return True


def goodbye(data):
    _speak(_engine.response("goodbye", BYE))
    return True


register("greet", greet)
register("how_are_you", how_are_you)
register("assistant_name", assistant_name)
register("welcome", welcome)
register("goodbye", goodbye)
