"""Controlled assistant-name normalization for spoken command routing."""

from __future__ import annotations

import re
from dataclasses import dataclass

from config import settings


@dataclass(frozen=True)
class AssistantInvocation:
    alias: str
    command: str

    @property
    def is_current_name(self) -> bool:
        return is_current_assistant_name(self.alias)

    @property
    def is_legacy_alias(self) -> bool:
        return is_legacy_assistant_alias(self.alias)


def get_assistant_name() -> str:
    return settings.get_assistant_name()


def get_assistant_name_lower() -> str:
    return settings.get_assistant_name_lower()


def get_assistant_aliases() -> tuple[str, ...]:
    return settings.get_assistant_aliases()


def is_current_assistant_name(value: str | None) -> bool:
    return bool(value) and str(value).casefold() == get_assistant_name_lower()


def is_legacy_assistant_alias(value: str | None) -> bool:
    return bool(value) and str(value).casefold() in {
        alias.casefold() for alias in settings.LEGACY_ASSISTANT_ALIASES
    }


def is_assistant_invocation(text: str | None) -> bool:
    return normalize_assistant_invocation(text) is not None


def strip_assistant_invocation(text: str | None) -> str:
    invocation = normalize_assistant_invocation(text)
    if invocation is None:
        return "" if text is None else " ".join(str(text).strip().split())
    return invocation.command


def _invocation_pattern() -> re.Pattern[str]:
    aliases = sorted(get_assistant_aliases(), key=len, reverse=True)
    escaped_aliases = "|".join(re.escape(alias) for alias in aliases)
    return re.compile(
        rf"^(?:(?:hey|hello)\s+)?"
        rf"(?P<alias>{escaped_aliases})"
        rf"(?=$|[\s,:;.!?])"
        rf"(?P<command>.*)$",
        re.IGNORECASE,
    )


def normalize_assistant_invocation(text: str | None) -> AssistantInvocation | None:
    """Extract a leading assistant invocation using only known aliases."""

    if text is None:
        return None

    normalized = " ".join(str(text).strip().split())
    match = _invocation_pattern().match(normalized)

    if not match:
        return None

    command = match.group("command").lstrip(" \t,:;.!?").strip()

    return AssistantInvocation(
        alias=match.group("alias").lower(),
        command=command,
    )


# * Compatibility exports. They are derived views, not independent identity
# * configuration, and existing callers can continue importing them.
CANONICAL_ASSISTANT_NAME = get_assistant_name_lower()
ASSISTANT_NAME_ALIASES = get_assistant_aliases()
