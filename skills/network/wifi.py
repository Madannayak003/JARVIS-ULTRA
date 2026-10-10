"""
JARVIS PRO
Wi-Fi Skill

Controls and reports Windows Wi-Fi state.
"""

import subprocess

from core.registry import register
from voice.manager import speak


# * =========================================================
# * Helpers
# * =========================================================

def _run(command):
    """Run a Windows netsh command safely."""

    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=True,
    )


# * =========================================================
# * Wi-Fi Action
# * =========================================================

def wifi_action(data=None):
    """
    Handle Wi-Fi actions.

    Supported actions:
        wifi_on
        wifi_off
        wifi_status
        wifi_list
    """

    data = data or {}

    action = data.get("action", "").strip().lower()

    # * -----------------------------------------------------
    # * Wi-Fi ON
    # * -----------------------------------------------------

    if action == "wifi_on":

        result = _run(
            'netsh interface set interface "Wi-Fi" enable'
        )

        if result.returncode == 0:

            speak("Wi-Fi is turned on.")

            print("[WIFI] Enabled")

            return True

        print(
            f"[WIFI ERROR] Enable failed: "
            f"{result.stderr.strip()}"
        )

        speak("I couldn't turn Wi-Fi on.")

        return False

    # * -----------------------------------------------------
    # * Wi-Fi OFF
    # * -----------------------------------------------------

    if action == "wifi_off":

        result = _run(
            'netsh interface set interface "Wi-Fi" disable'
        )

        if result.returncode == 0:

            speak("Wi-Fi is turned off.")

            print("[WIFI] Disabled")

            return True

        print(
            f"[WIFI ERROR] Disable failed: "
            f"{result.stderr.strip()}"
        )

        speak("I couldn't turn Wi-Fi off.")

        return False

    # * -----------------------------------------------------
    # * Wi-Fi STATUS
    # * -----------------------------------------------------

    if action == "wifi_status":

        result = _run(
            "netsh wlan show interfaces"
        )

        output = result.stdout

        if result.returncode != 0:

            print(
                f"[WIFI ERROR] Status failed: "
                f"{result.stderr.strip()}"
            )

            speak(
                "I couldn't check the Wi-Fi status."
            )

            return False

        lower = output.lower()

        # * -------------------------------------------------
        # * Detect connection
        # * -------------------------------------------------

        if "state" in lower and "connected" in lower:

            ssid = None

            for line in output.splitlines():

                line = line.strip()

                if line.lower().startswith("ssid"):

                    parts = line.split(":", 1)

                    if len(parts) == 2:

                        ssid = parts[1].strip()

                    break

            if ssid:

                speak(
                    f"Wi-Fi is connected to {ssid}."
                )

                print(
                    f"[WIFI] Connected | SSID: {ssid}"
                )

            else:

                speak("Wi-Fi is connected.")

                print("[WIFI] Connected")

        else:

            speak("Wi-Fi is not connected.")

            print("[WIFI] Not connected")

        return True

    # * -----------------------------------------------------
    # * LIST AVAILABLE NETWORKS
    # * -----------------------------------------------------

    if action == "wifi_list":

        result = _run(
            "netsh wlan show networks"
        )

        if result.returncode != 0:

            print(
                f"[WIFI ERROR] Network scan failed: "
                f"{result.stderr.strip()}"
            )

            speak(
                "I couldn't scan for available Wi-Fi networks."
            )

            return False

        output = result.stdout

        print()
        print("========== AVAILABLE WI-FI ==========")
        print(output)
        print("=====================================")
        print()

        # * Count detected SSIDs approximately.
        networks = []

        for line in output.splitlines():

            line = line.strip()

            if line.lower().startswith("ssid"):

                parts = line.split(":", 1)

                if len(parts) == 2:

                    ssid = parts[1].strip()

                    if ssid:
                        networks.append(ssid)

        if networks:

            speak(
                f"I found {len(networks)} "
                "available Wi-Fi networks. "
                "I've listed them in the terminal."
            )

        else:

            speak(
                "I couldn't find any available Wi-Fi networks."
            )

        print(
            f"[WIFI] Networks found: {len(networks)}"
        )

        return True

    # * -----------------------------------------------------
    # * Unknown action
    # * -----------------------------------------------------

    print(
        f"[WIFI] Unknown action: {action!r}"
    )

    return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "wifi_on",
    wifi_action,
)

register(
    "wifi_off",
    wifi_action,
)

register(
    "wifi_status",
    wifi_action,
)

register(
    "wifi_list",
    wifi_action,
)