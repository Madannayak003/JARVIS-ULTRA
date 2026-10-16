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
from core.live_execution import is_live_execution
from io import BytesIO


_LIVE_SCREEN_REQUESTS: dict[str, dict] = {}


def _short_error(error) -> str:
    """Keep screen-vision failures diagnosable without dumping payloads."""

    text = " ".join(str(error or "").split())
    return text[:240] + ("…" if len(text) > 240 else "")


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

    data = data or {}
    request_id = str(data.get("_live_request_id", "")).strip() if isinstance(data, dict) else ""

    if is_live_execution() and request_id in _LIVE_SCREEN_REQUESTS:
        return dict(_LIVE_SCREEN_REQUESTS[request_id])

    # * -----------------------------------------------------
    # * Capture current screen
    # * -----------------------------------------------------

    print("[SCREEN VISION] Capturing screenshot")
    image = screen_vision.capture()

    if image is None:

        print("[SCREEN VISION] Analysis failed — screenshot unavailable")

        if is_live_execution():
            return {
                "ok": False,
                "status": "failed",
                "action": "screen_vision_analyze",
                "correlation_id": request_id,
                "message": "I couldn't access the current screen.",
            }
        return "I couldn't access the current screen."

    if is_live_execution():
        buffer = BytesIO()
        try:
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
        except Exception as exc:
            print(f"[SCREEN VISION] Analysis failed — {_short_error(exc)}")
            return {
                "ok": False,
                "status": "failed",
                "action": "screen_vision_analyze",
                "correlation_id": request_id,
                "message": f"The current screen image could not be prepared for Live analysis: {exc}",
            }
        if not image_bytes:
            print("[SCREEN VISION] Analysis failed — empty screenshot")
            return {
                "ok": False,
                "status": "failed",
                "action": "screen_vision_analyze",
                "correlation_id": request_id,
                "message": "The current screen capture contained no image data, so analysis was not completed.",
            }

        # Keep the image on the function response rather than sending it as a
        # separate realtime_input frame.  The Live SDK documents realtime
        # media as nondeterministically ordered; FunctionResponse.parts keeps
        # the captured frame correlated with this exact tool invocation.
        print("[SCREEN VISION] Image ready")
        result = {
            "ok": True,
            "status": "completed",
            "action": "screen_vision_analyze",
            "correlation_id": request_id,
            "_live_image_bytes": image_bytes,
            "_live_image_mime_type": "image/png",
            "message": (
                "The current screen image is attached to this tool response. "
                "Describe only what is visible in that image."
            ),
        }
        if request_id:
            _LIVE_SCREEN_REQUESTS[request_id] = result
        return result

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
        print(f"[SCREEN VISION] Analysis failed — {_short_error(e)}")

        return (
            "I couldn't analyze the current screen."
        )

    # * -----------------------------------------------------
    # AI Failure
    # * -----------------------------------------------------

    if not response.success:

        print(f"[SCREEN VISION] Analysis failed — {_short_error(response.error)}")

        return (
            "I couldn't analyze the current screen."
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

        debug_print("[SCREEN VISION] Screen context updated")

    except Exception as e:

        # ! Context storage must never break
        # * the existing screen vision feature.

        debug_print(f"[SCREEN VISION] Context update failed — {_short_error(e)}")

    # * -----------------------------------------------------
    # * Return natural response
    # * -----------------------------------------------------

    print("[SCREEN VISION] Analysis completed")
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
