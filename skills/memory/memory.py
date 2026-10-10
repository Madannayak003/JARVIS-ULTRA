"""
JARVIS PRO
Memory Skill

Handles:
- Remembering user information
- Recalling information
- Natural-language memory commands
- Listing stored memories
- Forgetting memories

The skill remains fast and keeps natural-language
interpretation lightweight.
"""

import re

from voice.manager import speak

from core.plugins import register as plugin_register
from core.registry import register as ai_register

from ai.memory_store import (
    remember,
    forget,
    get,
    list_all,
)


# * =========================================================
# * Helpers
# * =========================================================

def _recall(key):
    """Return a stored memory value."""

    try:

        memory = get(key)

        if memory:
            return memory.value

    except Exception as e:

        print(
            f"[MEMORY ERROR] Recall failed: {e}"
        )

    return None


def _list_memory():
    """Return all stored memories as key/value pairs."""

    try:

        return [
            (memory.key, memory.value)
            for memory in list_all()
        ]

    except Exception as e:

        print(
            f"[MEMORY ERROR] List failed: {e}"
        )

        return []


# * =========================================================
# * Natural Memory Command
# * =========================================================

def memory_command(query):
    """
    Handle natural-language memory commands.

    Examples:

        remember my name is Madan
        remember my favorite color is blue
        what's my name
        what is my favorite color
    """

    if not query:

        return False

    print(
        "[MEMORY] Query:",
        query,
    )

    query = str(query).strip()

    # ! Keep original text for debugging,
    # * use lowercase only for pattern matching.
    lowered = query.lower()

    # * =====================================================
    # * REMEMBER
    # * =====================================================

    patterns = [

        r"remember my (.+?) is (.+)",

        r"remember that my (.+?) is (.+)",

        r"please remember my (.+?) is (.+)",

        r"save my (.+?) as (.+)",

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            lowered,
        )

        if not match:
            continue

        key = match.group(1).strip()
        value = match.group(2).strip()

        if not key or not value:

            speak(
                "I need both the information name and its value."
            )

            return True

        print(
            "[MEMORY] Remember:",
            key,
            "=",
            value,
        )

        try:

            remember(
                key,
                value,
            )

            speak(
                f"I'll remember your {key}."
            )

            return True

        except Exception as e:

            print(
                f"[MEMORY ERROR] Save failed: {e}"
            )

            speak(
                "I couldn't save that to memory."
            )

            return False

    # * =====================================================
    # * RECALL
    # * =====================================================

    recall_patterns = [

        r"what(?:'s| is) my (.+)",

        r"do you remember my (.+)",

        r"tell me my (.+)",

        r"what do you know about my (.+)",

    ]

    for pattern in recall_patterns:

        match = re.search(
            pattern,
            lowered,
        )

        if not match:
            continue

        key = match.group(1).strip()

        if not key:

            speak(
                "What would you like me to remember?"
            )

            return True

        print(
            "[MEMORY] Looking for:",
            key,
        )

        value = _recall(key)

        print(
            "[MEMORY] Result:",
            value,
        )

        if value:

            speak(
                f"Your {key} is {value}."
            )

        else:

            speak(
                f"I don't know your {key} yet."
            )

        return True

    # * =====================================================
    # * LIST MEMORY
    # * =====================================================

    if (
        "what do you remember" in lowered
        or "show my memories" in lowered
        or "list my memories" in lowered
    ):

        memories = _list_memory()

        if not memories:

            speak(
                "I don't have anything stored in memory yet."
            )

            return True

        print(
            "\n[MEMORY] Stored memories:"
        )

        for key, value in memories:

            print(
                f" - {key}: {value}"
            )

        speak(
            f"I have {len(memories)} stored memories."
        )

        return True

    # * =====================================================
    # * No match
    # * =====================================================

    print(
        "[MEMORY] No pattern matched."
    )

    return False


# * =========================================================
# * Registry - AI Planner
# * =========================================================

def ai_remember(data=None):

    data = data or {}

    key = str(
        data.get("key", "")
    ).strip()

    value = str(
        data.get("value", "")
    ).strip()

    if not key or not value:

        speak(
            "I need both a memory name and a value."
        )

        return False

    try:

        remember(
            key,
            value,
        )

        print(
            f"[MEMORY] Saved: {key} = {value}"
        )

        speak(
            f"I'll remember your {key}."
        )

        return True

    except Exception as e:

        print(
            f"[MEMORY ERROR] Save failed: {e}"
        )

        speak(
            "I couldn't save that to memory."
        )

        return False


# * =========================================================
# * Registry - AI Planner Recall
# * =========================================================

def ai_recall(data=None):

    data = data or {}

    key = str(
        data.get("key", "")
    ).strip()

    if not key:

        speak(
            "What would you like me to remember?"
        )

        return False

    value = _recall(key)

    if value:

        speak(
            f"Your {key} is {value}."
        )

        return True

    speak(
        f"I don't know your {key} yet."
    )

    return True


# * =========================================================
# * Forget Memory
# * =========================================================

def ai_forget(data=None):

    data = data or {}

    key = str(
        data.get("key", "")
    ).strip()

    if not key:

        speak(
            "Tell me what you'd like me to forget."
        )

        return False

    try:

        result = forget(key)

        print(
            f"[MEMORY] Forget: {key} -> {result}"
        )

        speak(
            f"I've forgotten your {key}."
        )

        return True

    except Exception as e:

        print(
            f"[MEMORY ERROR] Forget failed: {e}"
        )

        speak(
            "I couldn't forget that memory."
        )

        return False


# * =========================================================
# * Plugin Registration
# * =========================================================

plugin_register(
    [
        "remember",
        "what is my",
        "what's my",
        "do you remember my",
        "tell me my",
        "show my memories",
        "what do you remember",
    ],
    memory_command,
)


# * =========================================================
# AI Registry
# * =========================================================

ai_register(
    "remember",
    ai_remember,
)

ai_register(
    "recall",
    ai_recall,
)

ai_register(
    "forget_memory",
    ai_forget,
)