"""
JARVIS PRO
HUD Events

Defines events that can be displayed by the HUD.

These events contain information only.
They do not execute JARVIS actions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class HUDEvent:

    name: str

    data: Dict[str, Any] = field(
        default_factory=dict
    )

    timestamp: str = field(
        default_factory=lambda:
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

    # * One logical HUD/activity event keeps the same identity across
    # * the desktop SSE bridge and the remote dashboard stream.
    event_id: str = field(
        default_factory=lambda: uuid4().hex
    )

    source: Optional[str] = None


# * =========================================================
# * Standard HUD Events
# * =========================================================

HUD_IDLE = "idle"

HUD_LISTENING = "listening"

HUD_THINKING = "thinking"

HUD_SPEAKING = "speaking"

HUD_EXECUTING = "executing"

HUD_TASK_STARTED = "task_started"

HUD_TASK_FINISHED = "task_finished"

HUD_TASK_FAILED = "task_failed"

HUD_VOICE_MODE_CHANGED = "voice_mode_changed"

HUD_AI_MODEL_CHANGED = "ai_model_changed"

HUD_COMMAND = "command"

HUD_RESPONSE = "response"

HUD_SYSTEM_UPDATE = "system_update"

HUD_SYSTEM_ACTIVITY = "system_activity"

HUD_PERSONAL_LINKS = "personal_links"

HUD_NOTIFICATION = "notification"

HUD_ERROR = "error"
