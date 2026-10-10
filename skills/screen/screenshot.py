"""
JARVIS PRO
Screenshot Skill

Captures the current screen and saves it to the
configured screenshot directory.
"""

from datetime import datetime

import pyautogui

from core.registry import register
from voice.manager import speak
from core.paths import SCREENSHOTS


# * =========================================================
# * Screenshot
# * =========================================================

def screenshot(data=None):
    """
    Capture the current screen.

    Registry action:
        screenshot
    """

    try:

        # * Make sure the directory exists.
        SCREENSHOTS.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = datetime.now().strftime(
            "Screenshot_%Y%m%d_%H%M%S.png"
        )

        filepath = SCREENSHOTS / filename

        image = pyautogui.screenshot()

        image.save(filepath)

        print(
            f"[SCREENSHOT] Saved: {filepath}"
        )

        speak(
            "Screenshot captured successfully."
        )

        return True

    except Exception as e:

        print(
            f"[SCREENSHOT ERROR] {e}"
        )

        speak(
            "I couldn't capture the screenshot."
        )

        return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "screenshot",
    screenshot,
)