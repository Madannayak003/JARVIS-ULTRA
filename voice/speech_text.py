"""Small, state-aware normalization helpers for spoken assistant output."""

from __future__ import annotations

import re
import json


_FENCE_PATTERN = re.compile(r"(```|~~~)")
_HORIZONTAL_RULE_PATTERN = re.compile(
    r"(?m)^\s*(?:[-*_]\s*){3,}$"
)


def clean_for_speech_stateful(
    text: str,
    in_code_block: bool = False,
) -> tuple[str, bool]:
    """Remove presentation syntax and fenced code for TTS only.

    ``in_code_block`` carries fenced-code state across streamed chunks. The
    original Markdown remains available to the UI and conversation history.
    """

    if not text:
        return "", bool(in_code_block)

    original = str(text)

    # * Also skip standalone structured lines in an otherwise conversational
    # * response, such as a JSON result printed after an explanation.
    visible_lines = []
    for line in original.splitlines():
        try:
            line_value = json.loads(line.strip())
        except (TypeError, ValueError, json.JSONDecodeError):
            line_value = None

        if isinstance(line_value, (dict, list)):
            continue

        visible_lines.append(line)

    original = "\n".join(visible_lines)
    if not original.strip():
        return "", bool(in_code_block)

    # ! Do not narrate a complete raw JSON/dictionary payload. Structured
    # * results remain available in the original UI/history representation.
    if not in_code_block:
        try:
            structured = json.loads(original.strip())
        except (TypeError, ValueError, json.JSONDecodeError):
            structured = None

        if isinstance(structured, (dict, list)):
            return "", False

    parts = _FENCE_PATTERN.split(original)
    spoken_parts = []
    inside_code = bool(in_code_block)

    for part in parts:
        if part in {"```", "~~~"}:
            inside_code = not inside_code
        elif not inside_code:
            spoken_parts.append(part)

    spoken = "".join(spoken_parts)
    spoken = _HORIZONTAL_RULE_PATTERN.sub(" ", spoken)

    # * Markdown links/images become their human-readable label.
    spoken = re.sub(
        r"!\[([^\]]*)\]\([^)]*\)",
        r"\1",
        spoken,
    )
    spoken = re.sub(
        r"\[([^\]]+)\]\([^)]*\)",
        r"\1",
        spoken,
    )

    # * Remove presentation markers while retaining the actual words.
    spoken = re.sub(r"(?m)^\s*#{1,6}\s+", "", spoken)
    spoken = re.sub(
        r"(?m)^\s*(?:[-*+]\s+|\d+[.)]\s+|>\s?)",
        "",
        spoken,
    )
    spoken = re.sub(r"(\*\*|__)(.*?)\1", r"\2", spoken)
    spoken = re.sub(
        r"(?<!\w)([*_])(?=\S)(.*?\S)\1(?!\w)",
        r"\2",
        spoken,
    )

    # * Inline code is still useful as a word, but its backticks are not.
    spoken = spoken.replace("`", "")

    # * Avoid reading formatting noise such as repeated punctuation.
    spoken = re.sub(r"([!?])\1+", r"\1", spoken)
    spoken = re.sub(r"([,.])\1{2,}", r"\1", spoken)
    spoken = re.sub(r"\s+", " ", spoken).strip()

    return spoken, inside_code


def clean_for_speech(text: str) -> str:
    """Return a complete, non-streaming spoken representation."""

    cleaned, _ = clean_for_speech_stateful(text)
    return cleaned
