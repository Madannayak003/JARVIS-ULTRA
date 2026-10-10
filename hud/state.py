"""
JARVIS PRO HUD
State Model
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HUDState:

    status: str = "idle"

    voice_mode: str = "online"

    ai_model: str = ""

    current_task: str = ""

    task_status: str = ""

    listening: bool = False

    speaking: bool = False

    thinking: bool = False

    executing: bool = False

    system: dict[str, Any] = field(
        default_factory=dict
    )

    notification: str = ""

    error: str = ""

    last_event: str = ""

    last_command: str = ""

    last_response: str = ""

    last_update: str = ""