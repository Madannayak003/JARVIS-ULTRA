"""
JARVIS PRO
Live Screen Vision Skill

Analyzes the current desktop directly from memory.

Unlike screenshot_ai, this skill does NOT:

- save a screenshot
- search for a previous screenshot
- analyze a PNG from disk

It captures the current screen once and sends the
image directly to the AI vision system.

The successful analysis is also stored in the
ScreenContextManager for later contextual use.
"""

from core.registry import register
from core.diagnostics import debug_print

from ai.core.service import ai_service

from skills.screen.screen_vision import screen_vision

from brain.screen_context import screen_context
from config.settings import get_assistant_display_name
from core.live_execution import is_live_execution, schedule_live_task
from google.genai import types
from io import BytesIO


# * =========================================================
# * Live Screen Analysis
# * =========================================================

def screen_vision_analyze(data=None):
    """
    Analyze the current computer screen.

    The screen is captured directly into memory and
    passed to the multimodal AI system.

    The resulting analysis is stored as screen context.
    """

    # * -----------------------------------------------------
    # * Capture current screen
    # * -----------------------------------------------------

    image = screen_vision.capture()

    if image is None:

        print(
            "[SCREEN VISION] Unable to capture current screen."
        )

        return (
            "I couldn't access the current screen."
        )

    if is_live_execution():
        buffer = BytesIO()
        image.save(buffer, format="PNG")

        async def send_frame():
            from core.live_execution import get_live_session_context
            session, _loop, _tasks = get_live_session_context()
            if session is None:
                return
            await session.send_realtime_input(
                video=types.Blob(data=buffer.getvalue(), mime_type="image/png")
            )

        if schedule_live_task(send_frame()):
            return {
                "ok": True,
                "status": "pending_analysis",
                "action": "screen_vision_analyze",
                "message": "The current screen was captured and supplied to Gemini Live for analysis.",
            }
        return {"ok": False, "status": "failed", "message": "The Live screen channel is unavailable."}

    # * -----------------------------------------------------
    # AI Analysis
    # * -----------------------------------------------------

    try:

        response = ai_service.generate(
            prompt=(
                "Analyze this screen.\n\n"
                "Identify:\n"
                "1. The main application or window.\n"
                "2. What the user appears to be doing.\n"
                "3. Important visible text, errors, or status.\n"
                "4. Anything actionable or relevant.\n\n"
                "Be concise.\n"
                "Only mention information clearly visible on screen.\n"
                "Do not describe decorative details."
            ),
            system_prompt=(
                f"You are {get_assistant_display_name()}'s fast live screen-vision assistant. "
                "Accurately understand the supplied desktop image. "
                "Respond naturally and concisely. "
                "Prioritize useful information over visual detail. "
                "Never invent information that is not visible."
            ),
            capability="screen_vision",
            provider="gemini",
            model="gemini-3.5-flash-lite",
            images=[image],
        )

    except Exception as e:

        print(
            f"[SCREEN VISION AI ERROR] {e}"
        )

        return (
            "I couldn't analyze the current screen."
        )

    # * -----------------------------------------------------
    # AI Failure
    # * -----------------------------------------------------

    if not response.success:

        print(
            "[SCREEN VISION AI] Generation failed:",
            response.error,
        )

        return (
            "I couldn't analyze the current screen."
        )

    # * -----------------------------------------------------
    # * Diagnostics
    # * -----------------------------------------------------

    print(
        "[SCREEN VISION AI] Provider:",
        response.provider,
    )

    print(
        "[SCREEN VISION AI] Model:",
        response.model,
    )

    # * -----------------------------------------------------
    # * Empty response
    # * -----------------------------------------------------

    if not response.text:

        return (
            "I couldn't get a useful description "
            "of the current screen."
        )

    # * -----------------------------------------------------
    # * Final Analysis
    # * -----------------------------------------------------

    analysis = response.text.strip()

    # * -----------------------------------------------------
    # * Store Screen Context
    #
    # ! IMPORTANT:
    # * The existing captured image is NOT captured again.
    # * Only the AI's understanding is stored.
    # * -----------------------------------------------------

    try:

        screen_context.set_context({

            "analysis": analysis,

            "provider": response.provider,

            "model": response.model,

            "resolution": (
                image.size
                if hasattr(image, "size")
                else None
            ),

            "source": "live_screen",

        })

        print(
            "[SCREEN CONTEXT] Updated."
        )

    except Exception as e:

        # ! Context storage must never break
        # * the existing screen vision feature.

        print(
            f"[SCREEN CONTEXT ERROR] {e}"
        )

    # * -----------------------------------------------------
    # * Return natural response
    # * -----------------------------------------------------

    return analysis


# * =========================================================
# * Registry
# * =========================================================

register(
    "screen_vision_analyze",
    screen_vision_analyze,
    category="screen",
)

debug_print(
    "[SCREEN VISION SKILL] Registered."
)
