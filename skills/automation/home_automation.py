"""
JARVIS PRO - Home Automation
Mark-L-main automation adapted for JARVIS PRO.

Place at:
    skills/automation/home_automation.py

This does NOT replace any existing JARVIS skill.
Set JARVIS_ESP32_IP in the environment instead of hard-coding
the ESP32 address.
"""

import requests
from core.registry import register
from config.environment import get_env

ESP32_IP = get_env("JARVIS_ESP32_IP", "192.168.31.226")

BASE_URL = f"http://{ESP32_IP}"

HTTP_TIMEOUT = 3.0


def _endpoint(device: str, state: str) -> str:
    if not BASE_URL:
        raise RuntimeError(
            "JARVIS_ESP32_IP is not configured."
        )

    device = device.strip().lower()
    state = state.strip().upper()

    if device not in {"light", "fan"}:
        raise ValueError(
            f"Unsupported device: {device}. "
            "Currently supported: light, fan."
        )

    if state not in {"ON", "OFF"}:
        raise ValueError("State must be ON or OFF.")

    return f"{BASE_URL}/{device}/{state}"


def control_device(device: str, state: str) -> bool:
    """Control one supported ESP32 device."""
    url = _endpoint(device, state)

    try:
        response = requests.get(
            url,
            timeout=HTTP_TIMEOUT,
        )
        return response.status_code == 200

    except requests.RequestException as exc:
        print(f"[AUTOMATION] ESP32 request failed: {exc}")
        return False


def get_hardware_status():
    """Return ESP32 /status JSON, or None when unavailable."""
    if not BASE_URL:
        return None

    try:
        response = requests.get(
            f"{BASE_URL}/status",
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code != 200:
            return None
        return response.json()

    except (requests.RequestException, ValueError):
        return None


def home_automation(data=None):
    """
    Registry action.

    Examples:
        {
            "action": "home_automation",
            "device": "light",
            "command": "turn_on"
        }

        {
            "action": "home_automation",
            "device": "fan",
            "command": "turn_off"
        }

        {
            "action": "home_automation",
            "command": "status"
        }
    """

    data = data if isinstance(data, dict) else {}

    # * -----------------------------------------------------
    # * Read command separately from registry action
    # * -----------------------------------------------------

    command = str(
        data.get(
            "command",
            ""
        )
    ).strip().lower()

    # * Backward compatibility:
    # * If somebody directly calls the skill using
    # * {"action": "turn_on"}, still support it.
    if not command:

        command = str(
            data.get(
                "action",
                ""
            )
        ).strip().lower()

    # * -----------------------------------------------------
    # * STATUS
    # * -----------------------------------------------------

    if command == "status":

        status = get_hardware_status()

        return (
            status
            if status is not None
            else {
                "ok": False,
                "error":
                    "ESP32 is unreachable or not configured.",
            }
        )

    # * -----------------------------------------------------
    # * Device
    # * -----------------------------------------------------

    device = str(
        data.get(
            "device",
            ""
        )
    ).strip().lower()

    if not device:
        return (
            "Please specify a device, "
            "such as light, led, or fan."
        )

    # * light and led are the same physical device
    if device in ("light", "led"):
        device = "light"

    # * -----------------------------------------------------
    # * State
    # * -----------------------------------------------------

    if any(
        word in command
        for word in (
            "on",
            "enable",
            "start",
        )
    ):

        state = "ON"

    elif any(
        word in command
        for word in (
            "off",
            "disable",
            "stop",
        )
    ):

        state = "OFF"

    else:

        return (
            "Please specify ON or OFF."
        )

    # * -----------------------------------------------------
    # * Execute hardware command
    # * -----------------------------------------------------

    try:

        ok = control_device(
            device,
            state,
        )

    except (
        RuntimeError,
        ValueError,
    ) as exc:

        print(
            "[AUTOMATION ERROR]",
            exc,
        )

        return str(exc)

    # * -----------------------------------------------------
    # * Success
    # * -----------------------------------------------------

    if ok:

        return (
            f"{device} turned "
            f"{state.lower()}."
        )

    # * -----------------------------------------------------
    # * Failure
    # * -----------------------------------------------------

    return (
        f"I could not reach the ESP32 "
        f"to turn the {device} "
        f"{state.lower()}."
    )


register(
    "home_automation",
    home_automation,
    category="automation",
)
