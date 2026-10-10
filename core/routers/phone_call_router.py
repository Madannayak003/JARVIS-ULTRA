"""Deterministic routes for the dedicated Phone Call skill."""

from __future__ import annotations

import re


def _target_data(target: str) -> dict[str, str]:
    target = target.strip()
    number_like = re.sub(r"[+0-9\s().-]", "", target) == ""
    if number_like:
        return {"phone_number": target}
    target = re.sub(r"^my\s+", "", target).strip()
    return {"contact_name": target}


def phone_call_route(command):
    if not command:
        return None
    command = " ".join(str(command).strip().casefold().split())
    if not command:
        return None

    if command in {"answer call", "pick up", "accept call"}:
        return [{"action": "answer_call"}]
    if command in {"reject call", "decline call", "hang up incoming call"}:
        return [{"action": "reject_call"}]
    if command in {"end call", "hang up"}:
        return [{"action": "end_call"}]
    if command in {"call status", "phone call status"}:
        return [{"action": "call_status"}]
    if command in {
        "did i miss any calls",
        "who called me",
        "show missed calls",
        "missed calls",
    }:
        return [{"action": "missed_calls"}]

    match = re.fullmatch(
        r"(?:call|dial|make\s+(?:a\s+)?(?:phone\s+)?call\s+to)\s+(.+)",
        command,
    )
    if not match:
        return None

    target = match.group(1).strip()
    target = re.sub(r"^this\s+number\s+", "", target).strip()
    target = re.sub(r"\s+now$", "", target).strip()
    if not target:
        return None
    data = _target_data(target)
    action = "phone_call_number" if "phone_number" in data else "phone_call_contact"
    return [{"action": action, **data}]
