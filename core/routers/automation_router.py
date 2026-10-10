"""
JARVIS PRO
Automation Router

Routes natural-language home automation commands
to the existing home_automation skill.
"""

from __future__ import annotations


# * =========================================================
# * SUPPORTED DEVICES
# * =========================================================

DEVICES = (
    "light",
    "led",
    "fan",
)


# * =========================================================
# * ROUTER
# * =========================================================

def automation_route(command):

    if not command:
        return None

    command = str(command).strip().lower()

    if not command:
        return None

    # * =====================================================
    # * STATUS
    # * =====================================================

    if command in (
        "automation status",
        "home automation status",
        "check automation status",
        "check home automation",
        "check home automation status",
        "hardware status",
        "check hardware status",
        "show automation status",
        "show home automation status",
    ):

        return [
            {
                "action": "home_automation",
                "command": "status",
            }
        ]

    # * =====================================================
    # * DEVICE COMMANDS
    # * =====================================================

    for device in DEVICES:

        # * -------------------------------------------------
        # * ON
        # * -------------------------------------------------

        if command in (
            f"{device} on",
            f"turn on {device}",
            f"turn on the {device}",
            f"turn the {device} on",
            f"switch on {device}",
            f"switch on the {device}",
            f"switch the {device} on",
            f"enable {device}",
            f"enable the {device}",
            f"start {device}",
            f"start the {device}",
        ):

            return [
                {
                    "action": "home_automation",
                    "device": device,
                    "command": "turn_on",
                }
            ]

        # * -------------------------------------------------
        # * OFF
        # * -------------------------------------------------

        if command in (
            f"{device} off",
            f"turn off {device}",
            f"turn off the {device}",
            f"turn the {device} off",
            f"switch off {device}",
            f"switch off the {device}",
            f"switch the {device} off",
            f"disable {device}",
            f"disable the {device}",
            f"stop {device}",
            f"stop the {device}",
        ):

            return [
                {
                    "action": "home_automation",
                    "device": device,
                    "command": "turn_off",
                }
            ]

    # * =====================================================
    # * NO MATCH
    # * =====================================================

    return None