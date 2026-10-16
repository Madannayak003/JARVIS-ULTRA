"""Conversation context helpers for Gemini Live session replacement."""

from __future__ import annotations

from typing import Any, Iterable


def merge_transcript_text(current: str, incoming: str) -> str:
    """Merge repeated or chunked transcription events without duplication."""

    incoming = " ".join(str(incoming or "").split()).strip()
    current = " ".join(str(current or "").split()).strip()
    if not incoming:
        return current
    if not current:
        return incoming
    if incoming == current or incoming in current:
        return current
    if current in incoming:
        return incoming
    return f"{current} {incoming}".strip()


def record_live_turn(
    conversation_manager: Any,
    user_text: str,
    assistant_text: str,
    turn_id: str,
    tool_results: Iterable[str] = (),
) -> bool:
    """Record one completed Live turn in the existing conversation manager."""

    if conversation_manager is None or not turn_id:
        return False

    messages = conversation_manager.get_all_messages()
    if any(
        isinstance(getattr(message, "metadata", None), dict)
        and message.metadata.get("live_turn_id") == turn_id
        for message in messages
    ):
        return False

    metadata = {
        "source": "gemini_live",
        "live_turn_id": turn_id,
    }
    clean_user = " ".join(str(user_text or "").split()).strip()
    clean_assistant = " ".join(str(assistant_text or "").split()).strip()
    clean_tools = [
        " ".join(str(result or "").split()).strip()
        for result in tool_results
        if str(result or "").strip()
    ]

    if clean_user:
        conversation_manager.add_user_message(clean_user, metadata=metadata)
    if clean_assistant:
        assistant_metadata = dict(metadata)
        if clean_tools:
            assistant_metadata["tool_results"] = clean_tools
        conversation_manager.add_assistant_message(
            clean_assistant,
            metadata=assistant_metadata,
        )
    return bool(clean_user or clean_assistant)


def recent_live_messages(conversation_manager: Any, limit: int = 10) -> list[dict[str, str]]:
    """Return recent stored turns in the roles accepted by Live context input."""

    if conversation_manager is None:
        return []

    result = []
    for message in conversation_manager.get_recent_messages(limit=limit):
        content = " ".join(str(getattr(message, "content", "") or "").split()).strip()
        if not content:
            continue
        role = "model" if getattr(message, "role", "") == "assistant" else "user"
        metadata = getattr(message, "metadata", None)
        if role == "model" and isinstance(metadata, dict):
            tool_results = metadata.get("tool_results") or []
            if tool_results:
                content = (
                    f"{content}\nRelevant tool results: "
                    + " | ".join(str(result) for result in tool_results)
                )
        result.append({"role": role, "content": content})
    return result
