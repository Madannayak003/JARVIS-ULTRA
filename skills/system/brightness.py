"""
JARVIS PRO
Brightness Skill

Controls and reports display brightness.
"""

import screen_brightness_control as sbc

from core.registry import register
from voice.manager import speak


# * =========================================================
# * Helpers
# * =========================================================

def current_brightness():
    """Return current brightness percentage."""

    values = sbc.get_brightness()

    if not values:
        raise RuntimeError("Brightness information unavailable")

    return int(round(values[0]))


def set_brightness(percent):
    """Set brightness safely between 0 and 100."""

    percent = max(0, min(100, int(percent)))

    sbc.set_brightness(percent)

    return percent


# * =========================================================
# * Brightness
# * =========================================================

def brightness(data=None):
    """
    Control or report display brightness.

    Supported data:

        {}
        {"direction": "up"}
        {"direction": "down"}
        {"direction": "status"}
        {"percent": 70}
    """

    if data is None:
        data = {}

    try:

        direction = str(
            data.get("direction", "")
        ).strip().lower()

        percent = data.get("percent")

        # * -------------------------------------------------
        # * Exact brightness
        # * -------------------------------------------------

        if percent is not None:

            try:
                percent = int(percent)
            except (TypeError, ValueError):

                speak(
                    "Please give me a valid brightness percentage."
                )

                return False

            percent = set_brightness(percent)

            speak(
                f"Brightness set to {percent} percent."
            )

            print(
                f"[BRIGHTNESS] Set: {percent}%"
            )

            return True

        # * -------------------------------------------------
        # * Current brightness
        # * -------------------------------------------------

        if direction in (
            "",
            "status",
            "current",
            "check",
        ):

            current = current_brightness()

            speak(
                f"Brightness is at {current} percent."
            )

            print(
                f"[BRIGHTNESS] Current: {current}%"
            )

            return True

        # * -------------------------------------------------
        # * Increase
        # * -------------------------------------------------

        if direction in (
            "up",
            "increase",
            "higher",
            "raise",
        ):

            current = current_brightness()

            new_level = min(
                100,
                current + 10,
            )

            set_brightness(new_level)

            speak(
                f"Brightness increased to "
                f"{new_level} percent."
            )

            print(
                f"[BRIGHTNESS] {current}% -> {new_level}%"
            )

            return True

        # * -------------------------------------------------
        # * Decrease
        # * -------------------------------------------------

        if direction in (
            "down",
            "decrease",
            "lower",
            "reduce",
        ):

            current = current_brightness()

            new_level = max(
                0,
                current - 10,
            )

            set_brightness(new_level)

            speak(
                f"Brightness decreased to "
                f"{new_level} percent."
            )

            print(
                f"[BRIGHTNESS] {current}% -> {new_level}%"
            )

            return True

        # * -------------------------------------------------
        # * Maximum
        # * -------------------------------------------------

        if direction in (
            "max",
            "maximum",
            "full",
        ):

            set_brightness(100)

            speak(
                "Brightness set to maximum."
            )

            print(
                "[BRIGHTNESS] Set: 100%"
            )

            return True

        # * -------------------------------------------------
        # * Minimum
        # * -------------------------------------------------

        if direction in (
            "min",
            "minimum",
            "lowest",
        ):

            set_brightness(0)

            speak(
                "Brightness set to minimum."
            )

            print(
                "[BRIGHTNESS] Set: 0%"
            )

            return True

        # * -------------------------------------------------
        # * Unknown direction
        # * -------------------------------------------------

        speak(
            "I can increase, decrease, or set the brightness."
        )

        return False

    except Exception as e:

        print(
            f"[BRIGHTNESS ERROR] {e}"
        )

        speak(
            "I couldn't change the brightness."
        )

        return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "brightness",
    brightness,
)