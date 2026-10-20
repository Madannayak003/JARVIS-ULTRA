"""Deterministic HUD voice intents used before general Live tool dispatch."""

import re
from typing import Optional


def classify_hud_voice_intent(text: str) -> Optional[dict[str, str]]:
    """Classify only explicit ULTRON/APEX mode and assembly requests."""
    normalized = re.sub(r"\s+", " ", str(text or "").lower()).strip()
    if not normalized:
        return None

    if re.search(
        r"\b(?:reassemble|re[- ]?assemble|assemble again|replay (?:the )?(?:humanoid|apex)? ?assembly|show (?:the )?(?:humanoid|apex)? ?assembly)\b",
        normalized,
    ):
        return {
            "type": "assembly",
            "confirmation": "Reassembling the humanoid.",
        }

    mode_request = re.search(
        r"\b(?:switch|change|activate|enable|select|use|show|return|go)\b"
        r".{0,32}\b(apex|apex humanoid|humanoid|ultron|ultram)\b",
        normalized,
    )
    if not mode_request:
        return None

    target = mode_request.group(1)
    if target in {"ultron", "ultram"}:
        return {
            "type": "mode",
            "mode": "ultron",
            "confirmation": "Switching to ULTRON.",
        }

    return {
        "type": "mode",
        "mode": "apex",
        "confirmation": "Switching to APEX humanoid.",
    }
