import re

from core.assistant_name import get_assistant_aliases
from core.skill_categories import LOCAL_APPLICATIONS

SYSTEM = {

    # * ---------------------------------------------------------
    # * JARVIS APPLICATION SHUTDOWN
    # * ---------------------------------------------------------

    "shutdown": {
        "action": "terminate_jarvis"
    },

    "terminate": {
        "action": "terminate_jarvis"
    },

    "go terminate": {
        "action": "terminate_jarvis"
    },

    "close jarvis": {
        "action": "terminate_jarvis"
    },

    "exit jarvis": {
        "action": "terminate_jarvis"
    },

    "quit jarvis": {
        "action": "terminate_jarvis"
    },

    # * ---------------------------------------------------------
    # * SYSTEM ACTIONS
    # * ---------------------------------------------------------

    "restart": {
        "action": "restart"
    },

    "sleep": {
        "action": "sleep"
    },

    "lock": {
        "action": "lock"
    },

    "battery": {
        "action": "battery"
    },

    "battery status": {
        "action": "battery"
    },

    "show battery": {
        "action": "battery"
    },

    "show battery status": {
        "action": "battery"
    },

    "brightness up": {
        "action": "brightness",
        "direction": "up"
    },

    "brightness down": {
        "action": "brightness",
        "direction": "down"
    },

    "increase brightness": {
        "action": "brightness",
        "direction": "up"
    },

    "decrease brightness": {
        "action": "brightness",
        "direction": "down"
    },

    "increase volume": {
        "action": "volume",
        "direction": "up"
    },

    "decrease volume": {
        "action": "volume",
        "direction": "down"
    },

    "screenshot": {
        "action": "screenshot"
    },

    "take screenshot": {
        "action": "screenshot"
    },

    "time": {
        "action": "time"
    },

    "what time is it": {
        "action": "time"
    },

    "current time": {
        "action": "time"
    },

    "date": {
        "action": "date"
    },

    "start agent": {
        "action": "start_agent"
    },

    "stop agent": {
        "action": "stop_agent"
    },

    "agent status": {
        "action": "agent_status"
    },
}


def system_route(command):

    command = command.lower().strip()

    if command.startswith("close "):
        app = command[len("close "):].strip()
        if app in LOCAL_APPLICATIONS:
            return [
                {
                    "action": "close_process",
                    "process": app,
                }
            ]

    assistant_shutdown_commands = {
        f"{prefix} {alias}"
        for prefix in ("close", "exit", "quit")
        for alias in get_assistant_aliases()
    }
    if command in assistant_shutdown_commands:
        return [{"action": "terminate_jarvis"}]

    # * ---------- Lock ----------

    if command in [
        "lock",
        "lock computer",
        "lock pc",
        "lock laptop",
        "lock screen",
    ]:
        return [{"action": "lock"}]

    # * ---------- Windows Shutdown ----------

    if command in [
        "shutdown computer",
        "shutdown pc",
        "shutdown system",
        "shut down computer",
        "shut down system",
        "power off computer",
        "power off system",
    ]:
        return [{"action": "shutdown"}]

    # * ---------- Restart ----------

    if command in [
        "restart",
        "restart computer",
        "restart pc",
    ]:
        return [{"action": "restart"}]

    # * ---------- Sleep ----------

    if command in [
        "sleep",
        "sleep computer",
        "sleep pc",
    ]:
        return [{"action": "sleep"}]
    
    # * ---------- Fixed Volume ----------

    match = re.fullmatch(
        r"(?:set|change)\s+(?:the\s+)?volume\s+(?:to\s+)?(\d{1,3})(?:\s*(?:percent|%))?",
        command,
    )

    if match:
        percent = int(match.group(1))

        if 0 <= percent <= 100:
            return [
                {
                    "action": "volume",
                    "percent": percent,
                }
            ]

        return None

    # * ---------- Fixed Brightness ----------

    match = re.fullmatch(
        r"(?:set|change)\s+(?:the\s+)?brightness\s+(?:to\s+)?(\d{1,3})(?:\s*(?:percent|%))?",
        command,
    )

    if match:
        percent = int(match.group(1))

        if 0 <= percent <= 100:
            return [
                {
                    "action": "brightness",
                    "percent": percent,
                }
            ]

        return None

    # * ---------- Exact system commands ----------

    if command in SYSTEM:
        return [SYSTEM[command]]

    return None
