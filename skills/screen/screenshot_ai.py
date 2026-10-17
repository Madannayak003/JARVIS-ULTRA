"""
JARVIS ULTRA
Screenshot AI Skill

Analyzes the latest captured screenshot using the
configured AI service.
"""

import os

from core.registry import register
from voice.manager import speak

from ai.core.service import ai_service

from core.paths import SCREENSHOTS
from core.live_execution import is_live_execution, get_live_session_context, schedule_live_task


# * =========================================================
# * Screenshot AI
# * =========================================================

def screenshot_ai(data=None):
    """
    Analyze the latest screenshot.
    """

    try:

        SCREENSHOTS.mkdir(
            parents=True,
            exist_ok=True,
        )

        files = sorted(
            SCREENSHOTS.glob("*.png"),
            key=os.path.getmtime,
        )

        # * -------------------------------------------------
        # * No screenshots
        # * -------------------------------------------------

        if not files:

            speak(
                "I couldn't find any screenshots to analyze."
            )

            return True

        latest = files[-1]

        print(
            "[SCREENSHOT AI] Analyzing:",
            latest,
        )

        # A Live tool call must not invoke the secondary AI router. The active
        # Gemini Live session receives the captured frame and performs the
        # analysis itself.
        if is_live_execution():
            return {"ok": False, "status": "unsupported", "message": "Screenshot-file analysis is not available inside Gemini Live."}

        response = ai_service.generate(

            prompt=str(latest),

            system_prompt=(
                "Describe what is visible in this screenshot "
                "clearly and naturally. Mention important "
                "text, applications, windows, or visual "
                "elements when available."
            ),

            capability="conversation",

        )

        # * -------------------------------------------------
        # AI failure
        # * -------------------------------------------------

        if not response.success:

            print(
                "[SCREENSHOT AI] Generation failed:",
                response.error,
            )

            speak(
                "I couldn't analyze the screenshot."
            )

            return False

        # * -------------------------------------------------
        # * Diagnostics
        # * -------------------------------------------------

        print(
            "[SCREENSHOT AI] Provider:",
            response.provider,
        )

        print(
            "[SCREENSHOT AI] Model:",
            response.model,
        )

        # * -------------------------------------------------
        # * Empty response
        # * -------------------------------------------------

        if not response.text:

            speak(
                "I couldn't get a useful description of the screenshot."
            )

            return False

        # * -------------------------------------------------
        # * Speak result
        # * -------------------------------------------------

        speak(
            response.text
        )

        return True

    except Exception as e:

        print(
            f"[SCREENSHOT AI ERROR] {e}"
        )

        speak(
            "Something went wrong while analyzing the screenshot."
        )

        return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "screenshot_ai",
    screenshot_ai,
)
