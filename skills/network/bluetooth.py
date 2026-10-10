"""
JARVIS PRO
Bluetooth Skill

Provides quick access to Windows Bluetooth settings.
"""

import subprocess

from core.registry import register
from voice.manager import speak


# * =========================================================
# * Bluetooth Action
# * =========================================================

def bluetooth_action(data=None):
    """
    Handle Bluetooth actions.

    Supported actions:
        bluetooth_status
        bluetooth_devices
    """

    data = data or {}

    action = data.get("action", "").strip().lower()

    # * -----------------------------------------------------
    # * Bluetooth Status
    # * -----------------------------------------------------

    if action == "bluetooth_status":

        try:

            subprocess.Popen(
                "start ms-settings:bluetooth",
                shell=True,
            )

            print("[BLUETOOTH] Settings opened")

            speak(
                "I've opened the Bluetooth settings."
            )

            return True

        except Exception as e:

            print(
                f"[BLUETOOTH ERROR] {e}"
            )

            speak(
                "I couldn't open the Bluetooth settings."
            )

            return False

    # * -----------------------------------------------------
    # * Bluetooth Devices
    # * -----------------------------------------------------

    if action == "bluetooth_devices":

        try:

            subprocess.Popen(
                "start ms-settings:bluetooth",
                shell=True,
            )

            print(
                "[BLUETOOTH] Device settings opened"
            )

            speak(
                "I've opened Bluetooth devices."
            )

            return True

        except Exception as e:

            print(
                f"[BLUETOOTH ERROR] {e}"
            )

            speak(
                "I couldn't open the Bluetooth devices."
            )

            return False

    # * -----------------------------------------------------
    # * Unknown action
    # * -----------------------------------------------------

    print(
        f"[BLUETOOTH] Unknown action: {action!r}"
    )

    return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "bluetooth_status",
    bluetooth_action,
)

register(
    "bluetooth_devices",
    bluetooth_action,
)