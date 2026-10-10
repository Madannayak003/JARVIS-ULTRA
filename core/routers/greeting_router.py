from core.assistant_name import (
    get_assistant_aliases,
    normalize_assistant_invocation,
)


def _with_assistant_aliases(phrases):
    """Keep greeting variants derived from the central alias set."""

    aliases = get_assistant_aliases()
    return set(
        phrases
        + [f"{phrase} {alias}" for phrase in phrases for alias in aliases]
        + [f"{alias} {phrase}" for phrase in phrases for alias in aliases]
    )


def greeting_route(command):
    command = command.lower().strip()

    invocation = normalize_assistant_invocation(command)
    if invocation:
        command = invocation.command or "hey"

    if command in _with_assistant_aliases([
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "good to see you",
    ]):
        return [{"action": "greet", "command": command}]

    if command in _with_assistant_aliases(["how are you"]):
        return [{"action": "how_are_you"}]

    if command in {
        "what is your name",
        "what's your name",
        "who are you",
        "tell me your name",
    }:
        return [{"action": "assistant_name"}]

    if command in _with_assistant_aliases(["thanks", "thank you"]):
        return [{"action": "welcome"}]

    if command in _with_assistant_aliases(["bye", "goodbye", "see you"]):
        return [{"action": "goodbye"}]

    return None
